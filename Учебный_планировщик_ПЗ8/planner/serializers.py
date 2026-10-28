from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Subject, Task
from .validators import validate_task_title, validate_task_status_transition


class SubjectSerializer(serializers.ModelSerializer):
    task_count = serializers.SerializerMethodField()

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError('Название дисциплины должно содержать не менее двух символов.')
        return value.strip()

    def get_task_count(self, obj):
        count = getattr(obj, 'task_count', None)
        return count if count is not None else obj.tasks.count()

    class Meta:
        model = Subject
        fields = ['id', 'name', 'description', 'task_count']


class TaskSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    def validate_title(self, value):
        try:
            return validate_task_title(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)

    def validate_subject(self, value):
        request = self.context.get('request')
        if request and value.owner_id != request.user.id:
            raise serializers.ValidationError('Выберите дисциплину из своего списка.')
        return value

    def validate_status(self, value):
        current_status = self.instance.status if self.instance is not None else None
        try:
            return validate_task_status_transition(current_status, value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'subject', 'subject_name', 'due_date',
            'status', 'status_label',
        ]
