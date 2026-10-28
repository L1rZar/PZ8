document.addEventListener('DOMContentLoaded', () => {
    const apiMessage = document.getElementById('api-message');
    const subjectsBody = document.getElementById('subjects-body');
    const tasksBody = document.getElementById('tasks-body');
    const subjectForm = document.getElementById('subject-form');
    const taskForm = document.getElementById('task-form');
    const csrf = document.querySelector('#csrf-token-form [name=csrfmiddlewaretoken]')?.value || '';
    let subjects = [];

    function showMessage(message, type = 'success') {
        apiMessage.className = `alert alert-${type}`;
        apiMessage.textContent = message;
        apiMessage.classList.remove('d-none');
        window.scrollTo({top: 0, behavior: 'smooth'});
    }

    async function api(url, options = {}) {
        const headers = {'Accept': 'application/json', ...(options.headers || {})};
        if (options.body && !(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
        if (options.method && !['GET', 'HEAD', 'OPTIONS'].includes(options.method.toUpperCase())) headers['X-CSRFToken'] = csrf;
        const response = await fetch(url, {...options, headers, credentials: 'same-origin'});
        let data = null;
        try { data = await response.json(); } catch (_) { /* API response may be empty */ }
        if (!response.ok) {
            const detail = data && typeof data === 'object'
                ? Object.entries(data).map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(' ') : typeof value === 'object' ? JSON.stringify(value) : value}`).join(' · ')
                : '';
            throw new Error(detail || `Ошибка запроса (${response.status}).`);
        }
        return data;
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
    }

    function fillSubjectSelects() {
        const formSelect = document.getElementById('task-subject');
        const filterSelect = document.getElementById('filter-subject');
        const currentForm = formSelect.value;
        const currentFilter = filterSelect.value;
        formSelect.innerHTML = '<option value="">Выберите дисциплину</option>' + subjects.map(s => `<option value="${s.id}">${escapeHtml(s.name)}</option>`).join('');
        filterSelect.innerHTML = '<option value="">Все дисциплины</option>' + subjects.map(s => `<option value="${s.id}">${escapeHtml(s.name)}</option>`).join('');
        if (subjects.some(s => String(s.id) === currentForm)) formSelect.value = currentForm;
        if (subjects.some(s => String(s.id) === currentFilter)) filterSelect.value = currentFilter;
    }

    async function loadSubjects() {
        subjects = await api('/api/subjects/');
        document.getElementById('subject-count').textContent = `${subjects.length} дисциплин`;
        fillSubjectSelects();
        if (!subjects.length) {
            subjectsBody.innerHTML = '<tr><td colspan="5" class="text-secondary">Дисциплин пока нет. Добавьте первую с помощью формы.</td></tr>';
            return;
        }
        subjectsBody.innerHTML = subjects.map(s => `<tr>
            <td>${s.id}</td><td class="fw-semibold">${escapeHtml(s.name)}</td><td>${escapeHtml(s.description || '—')}</td><td>${s.task_count ?? 0}</td>
            <td class="text-nowrap"><button class="btn btn-sm btn-outline-primary me-1" data-edit-subject="${s.id}">Изменить</button><button class="btn btn-sm btn-outline-danger" data-delete-subject="${s.id}" data-name="${escapeHtml(s.name)}">Удалить</button></td>
        </tr>`).join('');
    }

    function filterParams() {
        const params = new URLSearchParams();
        const values = {
            search: document.getElementById('filter-search').value.trim(),
            status: document.getElementById('filter-status').value,
            subject: document.getElementById('filter-subject').value,
            due_after: document.getElementById('filter-after').value,
            due_before: document.getElementById('filter-before').value,
            ordering: document.getElementById('filter-ordering').value
        };
        Object.entries(values).forEach(([key, value]) => { if (value) params.set(key, value); });
        return params.toString();
    }

    async function loadTasks() {
        tasksBody.innerHTML = '<tr><td colspan="6" class="text-secondary">Загрузка...</td></tr>';
        const query = filterParams();
        try {
            const tasks = await api(`/api/tasks/${query ? `?${query}` : ''}`);
            document.getElementById('task-count').textContent = `${tasks.length} заданий`;
            const activeFilters = ['filter-search', 'filter-status', 'filter-subject', 'filter-after', 'filter-before'].filter(id => document.getElementById(id).value).length;
            document.getElementById('filter-summary').textContent = activeFilters ? `Активных фильтров: ${activeFilters}` : 'Фильтры не заданы';
            if (!tasks.length) {
                tasksBody.innerHTML = '<tr><td colspan="6"><div class="empty py-3"><p class="empty-title">Задания не найдены</p><p class="empty-subtitle text-secondary">Измените параметры фильтрации или добавьте задание.</p></div></td></tr>';
                return;
            }
            tasksBody.innerHTML = tasks.map(t => `<tr>
                <td>${t.id}</td><td class="fw-semibold">${escapeHtml(t.title)}</td><td>${escapeHtml(t.subject_name)}</td><td>${escapeHtml(t.due_date)}</td>
                <td><span class="badge ${t.status === 'completed' ? 'bg-success-lt' : t.status === 'in_progress' ? 'bg-azure-lt' : 'bg-secondary-lt'}">${escapeHtml(t.status_label)}</span></td>
                <td class="text-nowrap"><button class="btn btn-sm btn-outline-primary me-1" data-edit-task="${t.id}">Изменить</button><button class="btn btn-sm btn-outline-danger" data-delete-task="${t.id}" data-name="${escapeHtml(t.title)}">Удалить</button></td>
            </tr>`).join('');
        } catch (error) {
            tasksBody.innerHTML = `<tr><td colspan="6" class="text-danger">${escapeHtml(error.message)}</td></tr>`;
            showMessage(`Не удалось загрузить задания: ${error.message}`, 'danger');
        }
    }

    function resetSubjectForm() {
        subjectForm.reset();
        document.getElementById('subject-id').value = '';
        document.getElementById('subject-submit').textContent = 'Добавить';
    }
    function setAllowedStatusOptions(currentStatus) {
        const select = document.getElementById('task-status');
        const options = {
            new: [['new', 'Новое'], ['in_progress', 'В работе']],
            in_progress: [['new', 'Новое'], ['in_progress', 'В работе'], ['completed', 'Выполнено']],
            completed: [['in_progress', 'В работе'], ['completed', 'Выполнено']]
        };
        select.innerHTML = (options[currentStatus] || options.new)
            .map(([value, label]) => `<option value="${value}">${label}</option>`).join('');
        select.value = currentStatus || 'new';
    }

    function resetTaskForm() {
        taskForm.reset();
        document.getElementById('task-id').value = '';
        setAllowedStatusOptions('new');
        document.getElementById('task-status').disabled = true;
        document.getElementById('task-status-hint').textContent = 'Новое задание начинается со статуса «Новое».';
        document.getElementById('task-submit').textContent = 'Добавить задание';
    }

    subjectForm.addEventListener('submit', async event => {
        event.preventDefault();
        const id = document.getElementById('subject-id').value;
        const payload = {name: document.getElementById('subject-name').value.trim(), description: document.getElementById('subject-description').value.trim()};
        try {
            await api(id ? `/api/subjects/${id}/` : '/api/subjects/', {method: id ? 'PUT' : 'POST', body: JSON.stringify(payload)});
            resetSubjectForm();
            await loadSubjects();
            await loadTasks();
            showMessage(id ? 'Дисциплина изменена через REST API.' : 'Дисциплина добавлена через REST API.');
        } catch (error) { showMessage(`Не удалось сохранить дисциплину: ${error.message}`, 'danger'); }
    });

    document.getElementById('subject-cancel').addEventListener('click', resetSubjectForm);
    subjectsBody.addEventListener('click', async event => {
        const edit = event.target.closest('[data-edit-subject]');
        const remove = event.target.closest('[data-delete-subject]');
        if (edit) {
            const s = subjects.find(item => item.id === Number(edit.dataset.editSubject));
            if (!s) return;
            document.getElementById('subject-id').value = s.id;
            document.getElementById('subject-name').value = s.name;
            document.getElementById('subject-description').value = s.description || '';
            document.getElementById('subject-submit').textContent = 'Сохранить изменения';
            subjectForm.scrollIntoView({behavior: 'smooth', block: 'center'});
        }
        if (remove) {
            if (!window.confirm(`Удалить дисциплину «${remove.dataset.name}»? Если к ней привязаны задания, сервер не позволит удалить её.`)) return;
            try {
                await api(`/api/subjects/${remove.dataset.deleteSubject}/`, {method: 'DELETE'});
                await loadSubjects(); await loadTasks();
                showMessage('Дисциплина удалена.');
            } catch (error) { showMessage(`Не удалось удалить дисциплину: ${error.message}`, 'danger'); }
        }
    });

    taskForm.addEventListener('submit', async event => {
        event.preventDefault();
        const id = document.getElementById('task-id').value;
        const payload = {
            title: document.getElementById('task-title').value.trim(),
            subject: Number(document.getElementById('task-subject').value),
            due_date: document.getElementById('task-due-date').value,
            status: id ? document.getElementById('task-status').value : 'new'
        };
        try {
            await api(id ? `/api/tasks/${id}/` : '/api/tasks/', {method: id ? 'PUT' : 'POST', body: JSON.stringify(payload)});
            resetTaskForm(); await loadSubjects(); await loadTasks();
            showMessage(id ? 'Задание изменено через REST API.' : 'Задание добавлено через REST API.');
        } catch (error) { showMessage(`Не удалось сохранить задание: ${error.message}`, 'danger'); }
    });

    document.getElementById('task-cancel').addEventListener('click', resetTaskForm);
    tasksBody.addEventListener('click', async event => {
        const edit = event.target.closest('[data-edit-task]');
        const remove = event.target.closest('[data-delete-task]');
        if (edit) {
            try {
                const task = await api(`/api/tasks/${edit.dataset.editTask}/`);
                document.getElementById('task-id').value = task.id;
                document.getElementById('task-title').value = task.title;
                document.getElementById('task-subject').value = task.subject;
                document.getElementById('task-due-date').value = task.due_date;
                setAllowedStatusOptions(task.status);
                document.getElementById('task-status').disabled = false;
                document.getElementById('task-status-hint').textContent = 'Статус можно изменить только на соседний этап.';
                document.getElementById('task-submit').textContent = 'Сохранить изменения';
                taskForm.scrollIntoView({behavior: 'smooth', block: 'center'});
            } catch (error) { showMessage(`Не удалось получить задание: ${error.message}`, 'danger'); }
        }
        if (remove) {
            if (!window.confirm(`Вы действительно хотите удалить задание «${remove.dataset.name}»?`)) return;
            try {
                await api(`/api/tasks/${remove.dataset.deleteTask}/`, {method: 'DELETE'});
                await loadSubjects(); await loadTasks(); showMessage('Задание удалено.');
            } catch (error) { showMessage(`Не удалось удалить задание: ${error.message}`, 'danger'); }
        }
    });

    document.getElementById('task-filters').addEventListener('submit', event => { event.preventDefault(); loadTasks(); });
    document.getElementById('filters-reset').addEventListener('click', () => {
        document.getElementById('task-filters').reset();
        loadTasks();
    });

    (async function init() {
        try { await loadSubjects(); await loadTasks(); }
        catch (error) { showMessage(`Не удалось подключиться к REST API: ${error.message}. Убедитесь, что сервер запущен и Django REST Framework установлен.`, 'danger'); }
    })();
});
