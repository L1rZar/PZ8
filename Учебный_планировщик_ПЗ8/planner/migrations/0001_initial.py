# Generated for the study planner application.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Название дисциплины')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
            ],
            options={
                'verbose_name': 'Дисциплина',
                'verbose_name_plural': 'Дисциплины',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Название задания')),
                ('due_date', models.DateField(verbose_name='Срок выполнения')),
                ('status', models.CharField(choices=[('new', 'Новое'), ('in_progress', 'В работе'), ('completed', 'Выполнено')], default='new', max_length=20, verbose_name='Статус')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='tasks', to='planner.subject', verbose_name='Дисциплина')),
            ],
            options={
                'verbose_name': 'Задание',
                'verbose_name_plural': 'Задания',
                'ordering': ['due_date', 'title'],
            },
        ),
    ]
