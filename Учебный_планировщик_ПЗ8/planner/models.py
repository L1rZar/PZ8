from django.conf import settings
from django.db import models


class Subject(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='subjects', null=True, blank=True, verbose_name='Владелец',
    )
    name = models.CharField('Название дисциплины', max_length=150)
    description = models.TextField('Описание', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = 'Дисциплина'
        verbose_name_plural = 'Дисциплины'


class Task(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='tasks', null=True, blank=True, verbose_name='Владелец',
    )
    STATUS_CHOICES = [
        ('new', 'Новое'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнено'),
    ]

    title = models.CharField('Название задания', max_length=200)
    subject = models.ForeignKey(
        Subject,
        on_delete=models.PROTECT,
        related_name='tasks',
        verbose_name='Дисциплина',
    )
    due_date = models.DateField('Срок выполнения')
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['due_date', 'title']
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'
