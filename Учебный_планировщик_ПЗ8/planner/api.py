import re

from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.utils.dateparse import parse_date
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from .models import Subject, Task
from .serializers import SubjectSerializer, TaskSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Subject.objects.filter(owner=self.request.user).annotate(
            task_count=Count('tasks')
        ).order_by('name')
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError({'detail': 'Нельзя удалить дисциплину, пока к ней привязаны задания.'})


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Task.objects.filter(owner=self.request.user).select_related('subject')
        params = self.request.query_params

        search = params.get('search', '').strip()
        status = params.get('status', '').strip()
        subject = params.get('subject', '').strip()
        due_before = params.get('due_before', '').strip()
        due_after = params.get('due_after', '').strip()

        if search:
            queryset = queryset.filter(title__iregex=re.escape(search))
        if status:
            valid_statuses = dict(Task.STATUS_CHOICES)
            if status not in valid_statuses:
                raise ValidationError({'status': 'Недопустимый статус. Используйте new, in_progress или completed.'})
            queryset = queryset.filter(status=status)
        if subject:
            if not subject.isdigit():
                raise ValidationError({'subject': 'Укажите числовой идентификатор дисциплины.'})
            queryset = queryset.filter(subject_id=int(subject))
        if due_before:
            parsed = parse_date(due_before)
            if parsed is None:
                raise ValidationError({'due_before': 'Введите дату в формате ГГГГ-ММ-ДД.'})
            queryset = queryset.filter(due_date__lte=parsed)
        if due_after:
            parsed = parse_date(due_after)
            if parsed is None:
                raise ValidationError({'due_after': 'Введите дату в формате ГГГГ-ММ-ДД.'})
            queryset = queryset.filter(due_date__gte=parsed)

        ordering = params.get('ordering', 'due_date')
        allowed_ordering = {'due_date', '-due_date', 'title', '-title', 'status', '-status'}
        if ordering not in allowed_ordering:
            raise ValidationError({'ordering': 'Недопустимое поле сортировки.'})
        return queryset.order_by(ordering, 'id')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
