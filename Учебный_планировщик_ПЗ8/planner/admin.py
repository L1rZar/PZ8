from django.contrib import admin
from .models import Subject, Task


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'due_date', 'status')
    list_filter = ('status', 'subject', 'due_date')
    search_fields = ('title',)
