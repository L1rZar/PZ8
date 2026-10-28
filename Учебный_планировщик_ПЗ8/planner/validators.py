import re

from django.core.exceptions import ValidationError

# Разрешены Unicode-буквы, цифры, пробелы и распространённая пунктуация.
TASK_TITLE_PATTERN = re.compile(r'^(?:[^\W_]|[\s№.,:;()\-+/!?\'"])+$', flags=re.UNICODE)


def validate_task_title(value):
    title = (value or '').strip()
    if len(title) < 2:
        raise ValidationError('Название задания должно содержать не менее двух символов.')
    if not TASK_TITLE_PATTERN.fullmatch(title):
        raise ValidationError(
            'Используйте буквы, цифры, пробелы и обычные знаки пунктуации. '
            'Символы вроде ^, %, $, @ и _ не допускаются.'
        )
    return title


# Разрешены только последовательные переходы между статусами.
ALLOWED_STATUS_TRANSITIONS = {
    'new': ('new', 'in_progress'),
    'in_progress': ('new', 'in_progress', 'completed'),
    'completed': ('in_progress', 'completed'),
}

def allowed_task_statuses(current_status):
    if current_status is None:
        return ('new',)
    return ALLOWED_STATUS_TRANSITIONS.get(current_status, (current_status,))

def validate_task_status_transition(current_status, new_status):
    """Validate status changes for forms and API requests. None means creation."""
    if current_status is None:
        if new_status != 'new':
            raise ValidationError('Новое задание должно начинаться со статуса «Новое».')
        return new_status

    allowed = allowed_task_statuses(current_status)
    if new_status not in allowed:
        raise ValidationError(
            'Нельзя пропускать этапы выполнения. Сначала переведите задание в статус «В работе».'
            if current_status == 'new' and new_status == 'completed'
            else 'Недопустимый переход статуса. Возвращаться можно только на предыдущий этап.'
        )
    return new_status
