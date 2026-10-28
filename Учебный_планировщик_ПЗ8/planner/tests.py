from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Subject, Task


class PlannerAPITests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student', password='StrongPass123!')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.subject = Subject.objects.create(owner=self.user, name='Высшая математика', description='Тестовая дисциплина')
        self.other_subject = Subject.objects.create(owner=self.user, name='Базы данных')
        self.task = Task.objects.create(
            owner=self.user,
            title='Лабораторная работа № 6',
            subject=self.subject,
            due_date=date(2026, 11, 1),
            status='new',
        )
        Task.objects.create(
            owner=self.user,
            title='Подготовить конспект',
            subject=self.other_subject,
            due_date=date(2026, 12, 15),
            status='completed',
        )

    def test_subject_crud(self):
        response = self.client.post('/api/subjects/', {
            'name': 'Алгоритмы', 'description': 'Новая дисциплина'
        }, format='json')
        self.assertEqual(response.status_code, 201)
        subject_id = response.data['id']
        self.assertEqual(Subject.objects.get(pk=subject_id).owner, self.user)

        response = self.client.patch(f'/api/subjects/{subject_id}/', {'name': 'Алгоритмы и структуры данных'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'Алгоритмы и структуры данных')

        response = self.client.delete(f'/api/subjects/{subject_id}/')
        self.assertEqual(response.status_code, 204)

    def test_task_crud(self):
        response = self.client.post('/api/tasks/', {
            'title': 'ЛР2',
            'subject': self.subject.id,
            'due_date': '2026-11-20',
            'status': 'new',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        task_id = response.data['id']
        self.assertEqual(Task.objects.get(pk=task_id).owner, self.user)

        response = self.client.patch(f'/api/tasks/{task_id}/', {'status': 'in_progress'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'in_progress')

        response = self.client.patch(f'/api/tasks/{task_id}/', {'status': 'completed'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'completed')

        response = self.client.delete(f'/api/tasks/{task_id}/')
        self.assertEqual(response.status_code, 204)

    def test_task_title_validation(self):
        base_payload = {'subject': self.subject.id, 'due_date': '2026-11-20', 'status': 'new'}
        response = self.client.post('/api/tasks/', {**base_payload, 'title': 'А'}, format='json')
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/api/tasks/', {**base_payload, 'title': 'Задание@1'}, format='json')
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/api/tasks/', {**base_payload, 'title': 'ЛР2'}, format='json')
        self.assertEqual(response.status_code, 201)

    def test_task_status_transitions_must_be_sequential(self):
        create_response = self.client.post('/api/tasks/', {
            'title': 'Новая работа', 'subject': self.subject.id,
            'due_date': '2026-11-20', 'status': 'completed',
        }, format='json')
        self.assertEqual(create_response.status_code, 400)

        response = self.client.patch(f'/api/tasks/{self.task.id}/', {'status': 'completed'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'new')

        response = self.client.patch(f'/api/tasks/{self.task.id}/', {'status': 'in_progress'}, format='json')
        self.assertEqual(response.status_code, 200)
        response = self.client.patch(f'/api/tasks/{self.task.id}/', {'status': 'completed'}, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.patch(f'/api/tasks/{self.task.id}/', {'status': 'new'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'completed')

    def test_server_side_filters_can_be_combined(self):
        response = self.client.get('/api/tasks/', {
            'search': 'лабораторная', 'status': 'new', 'subject': self.subject.id,
            'due_before': '2026-11-30',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.task.id)

    def test_invalid_filter_returns_validation_error(self):
        response = self.client.get('/api/tasks/?status=unknown')
        self.assertEqual(response.status_code, 400)

    def test_subject_with_tasks_cannot_be_deleted(self):
        response = self.client.delete(f'/api/subjects/{self.subject.id}/')
        self.assertEqual(response.status_code, 400)
        self.assertTrue(Subject.objects.filter(pk=self.subject.id).exists())

    def test_user_cannot_access_another_users_records(self):
        other_user = User.objects.create_user(username='other', password='StrongPass123!')
        other_subject = Subject.objects.create(owner=other_user, name='Чужая дисциплина')
        other_task = Task.objects.create(owner=other_user, title='Чужая ЛР', subject=other_subject, due_date=date(2026, 12, 1))

        response = self.client.get('/api/subjects/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(other_subject.id, [item['id'] for item in response.data])
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(other_task.id, [item['id'] for item in response.data])
        response = self.client.get(f'/api/tasks/{other_task.id}/')
        self.assertEqual(response.status_code, 404)

    def test_api_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/tasks/')
        self.assertIn(response.status_code, (401, 403))
