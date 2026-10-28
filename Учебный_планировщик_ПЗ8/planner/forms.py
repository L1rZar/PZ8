from django import forms
from .models import Subject, Task
from .validators import validate_task_title, validate_task_status_transition, allowed_task_statuses


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например, Высшая математика',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Краткое описание дисциплины',
            }),
        }


class TaskForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['subject'].queryset = Subject.objects.filter(owner=user).order_by('name')
        if not self.instance.pk:
            self.fields['status'].choices = [('new', 'Новое')]
            self.initial.setdefault('status', 'new')
        else:
            allowed = set(allowed_task_statuses(self.instance.status))
            self.fields['status'].choices = [
                (value, label) for value, label in Task.STATUS_CHOICES if value in allowed
            ]

    def clean_title(self):
        return validate_task_title(self.cleaned_data.get('title'))

    def clean_status(self):
        status = self.cleaned_data.get('status')
        current_status = self.instance.status if self.instance.pk else None
        return validate_task_status_transition(current_status, status)

    class Meta:
        model = Task
        fields = ['title', 'subject', 'due_date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название задания',
            }),
            'subject': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
