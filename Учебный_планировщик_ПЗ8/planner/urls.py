from django.contrib.auth.views import LogoutView
from django.urls import path
from . import views

app_name = 'planner'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('accounts/login/', views.PlannerLoginView.as_view(), name='login'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('accounts/register/', views.register, name='register'),
    path('tasks/', views.task_list, name='tasks'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:task_id>/status/', views.task_change_status, name='task_change_status'),
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('subjects/', views.subject_list, name='subjects'),
    path('api-console/', views.api_console, name='api_console'),
]
