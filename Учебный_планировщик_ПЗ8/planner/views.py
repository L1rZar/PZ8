import json

from django.contrib import messages
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from .auth_forms import PlannerAuthenticationForm, PlannerUserCreationForm
from .forms import SubjectForm, TaskForm
from .models import Subject, Task
from .validators import validate_task_status_transition


def claim_legacy_data(user):
    """Attach records created before account support to the first account that uses them."""
    Subject.objects.filter(owner__isnull=True).update(owner=user)
    Task.objects.filter(owner__isnull=True).update(owner=user)


class PlannerLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = PlannerAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        claim_legacy_data(self.request.user)
        return response


def register(request):
    if request.user.is_authenticated:
        return redirect('planner:dashboard')
    if request.method == 'POST':
        form = PlannerUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            claim_legacy_data(user)
            messages.success(request, 'Аккаунт создан. Добро пожаловать!')
            return redirect('planner:dashboard')
    else:
        form = PlannerUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    today = timezone.localdate()
    tasks = Task.objects.filter(owner=request.user).select_related('subject')
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='completed').count()

    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'new_tasks': tasks.filter(status='new').count(),
        'in_progress_tasks': tasks.filter(status='in_progress').count(),
        'overdue_tasks': tasks.filter(due_date__lt=today).exclude(status='completed').count(),
        'subject_count': Subject.objects.filter(owner=request.user).count(),
        'completion_percent': round(completed_tasks / total_tasks * 100) if total_tasks else 0,
        'upcoming_tasks': tasks.filter(due_date__gte=today).exclude(status='completed').order_by('due_date')[:5],
    }
    return render(request, 'planner/dashboard.html', context)


@login_required
def task_list(request):
    tasks = Task.objects.filter(owner=request.user).select_related('subject')
    subjects = Subject.objects.filter(owner=request.user)
    return render(request, 'planner/tasks.html', {
        'tasks': tasks,
        'subjects': subjects,
        'form': TaskForm(user=request.user),
    })


@login_required
@require_POST
def task_create(request):
    form = TaskForm(request.POST, user=request.user)
    if not form.is_valid():
        return JsonResponse({'errors': form.errors.get_json_data()}, status=400)

    task = form.save(commit=False)
    task.owner = request.user
    task.save()
    task = Task.objects.select_related('subject').get(pk=task.pk)
    row_html = render_to_string('planner/includes/task_row.html', {'task': task}, request=request)
    return JsonResponse({'message': 'Задание успешно добавлено.', 'row_html': row_html}, status=201)


@login_required
def task_edit(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Задание успешно изменено.')
            return redirect('planner:tasks')
    else:
        form = TaskForm(instance=task, user=request.user)

    return render(request, 'planner/task_edit.html', {'form': form, 'task': task})


@login_required
@require_POST
def task_change_status(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Не удалось прочитать данные запроса.'}, status=400)

    status = data.get('status')
    allowed_statuses = dict(Task.STATUS_CHOICES)
    if status not in allowed_statuses:
        return JsonResponse({'error': 'Выбран неизвестный статус.'}, status=400)

    try:
        validate_task_status_transition(task.status, status)
    except DjangoValidationError as exc:
        return JsonResponse({'error': ' '.join(exc.messages)}, status=400)

    task.status = status
    task.save(update_fields=['status'])
    return JsonResponse({'message': 'Статус задания изменён.', 'status': task.status, 'status_label': task.get_status_display()})


@login_required
@require_POST
def task_delete(request, task_id):
    task = get_object_or_404(Task, pk=task_id, owner=request.user)
    task.delete()
    return JsonResponse({'message': 'Задание успешно удалено.'})


@login_required
def subject_list(request):
    subjects = Subject.objects.filter(owner=request.user).annotate(task_count=Count('tasks')).order_by('name')

    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.owner = request.user
            subject.save()
            messages.success(request, 'Дисциплина добавлена.')
            return redirect('planner:subjects')
    else:
        form = SubjectForm()

    return render(request, 'planner/subjects.html', {'subjects': subjects, 'form': form})


@login_required
def api_console(request):
    return render(request, 'planner/api_console.html')
