document.addEventListener('DOMContentLoaded', function () {
    const csrfInput = document.querySelector('#csrf-token-form [name=csrfmiddlewaretoken]');
    const csrfToken = csrfInput ? csrfInput.value : '';

    function showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `alert alert-${type} shadow-sm mb-2`;
        toast.setAttribute('role', type === 'danger' ? 'alert' : 'status');
        toast.textContent = message;
        container.appendChild(toast);
        window.setTimeout(() => toast.remove(), 3500);
    }

    async function readResponse(response) {
        const contentType = response.headers.get('content-type') || '';
        if (contentType.includes('application/json')) {
            return await response.json();
        }
        if (response.status === 404) {
            throw new Error('Запрошенный объект не найден.');
        }
        throw new Error('Сервер вернул неожиданный ответ.');
    }

    function showFieldErrors(errors) {
        Object.keys(errors).forEach(function (fieldName) {
            const element = document.querySelector(`[data-error-for="${fieldName}"]`);
            const input = document.querySelector(`[name="${fieldName}"]`);
            const messages = errors[fieldName].map(error => error.message).join(' ');

            if (element) element.textContent = messages;
            if (input) input.classList.add('is-invalid');
        });
    }

    function clearFieldErrors(form) {
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        form.querySelectorAll('[data-error-for]').forEach(el => el.textContent = '');
        const generalError = document.getElementById('task-form-error');
        if (generalError) generalError.textContent = '';
    }

    const searchInput = document.getElementById('task-search');
    const statusFilter = document.getElementById('task-status-filter');
    const subjectFilter = document.getElementById('task-subject-filter');
    const sortSelect = document.getElementById('task-sort');
    const resetButton = document.getElementById('reset-task-filters');

    const storageKeys = {
        search: 'planner_task_search',
        status: 'planner_task_status',
        subject: 'planner_task_subject',
        sort: 'planner_task_sort'
    };

    function loadSavedValue(key, element) {
        const value = localStorage.getItem(key);
        if (value !== null && Array.from(element.options).some(option => option.value === value)) {
            element.value = value;
        }
    }

    function applyTaskFilters() {
        const tbody = document.getElementById('task-table-body');
        if (!tbody || !searchInput || !statusFilter || !subjectFilter || !sortSelect) return;

        const rows = Array.from(tbody.querySelectorAll('[data-task-row]'));
        const search = searchInput.value.trim().toLowerCase();
        const status = statusFilter.value;
        const subject = subjectFilter.value;

        rows.forEach(function (row) {
            const matchesSearch = row.dataset.title.includes(search);
            const matchesStatus = !status || row.dataset.status === status;
            const matchesSubject = !subject || row.dataset.subject === subject;
            row.classList.toggle('task-row-hidden', !(matchesSearch && matchesStatus && matchesSubject));
        });

        rows.sort(function (a, b) {
            if (sortSelect.value === 'title') return a.dataset.title.localeCompare(b.dataset.title, 'ru');
            if (sortSelect.value === 'status') return a.dataset.status.localeCompare(b.dataset.status);
            return a.dataset.dueDate.localeCompare(b.dataset.dueDate);
        });
        rows.forEach(row => tbody.appendChild(row));

        const visibleCount = rows.filter(row => !row.classList.contains('task-row-hidden')).length;
        const counter = document.getElementById('visible-task-count');
        if (counter) counter.textContent = `${visibleCount} из ${rows.length}`;

        localStorage.setItem(storageKeys.search, searchInput.value);
        localStorage.setItem(storageKeys.status, statusFilter.value);
        localStorage.setItem(storageKeys.subject, subjectFilter.value);
        localStorage.setItem(storageKeys.sort, sortSelect.value);
    }

    if (searchInput && statusFilter && subjectFilter && sortSelect) {
        searchInput.value = localStorage.getItem(storageKeys.search) || '';
        loadSavedValue(storageKeys.status, statusFilter);
        loadSavedValue(storageKeys.subject, subjectFilter);
        loadSavedValue(storageKeys.sort, sortSelect);

        searchInput.addEventListener('input', applyTaskFilters);
        statusFilter.addEventListener('change', applyTaskFilters);
        subjectFilter.addEventListener('change', applyTaskFilters);
        sortSelect.addEventListener('change', applyTaskFilters);

        if (resetButton) {
            resetButton.addEventListener('click', function () {
                searchInput.value = '';
                statusFilter.value = '';
                subjectFilter.value = '';
                sortSelect.value = 'date';
                applyTaskFilters();
            });
        }
        applyTaskFilters();
    }

    // Создание задания без перезагрузки.
    const createForm = document.getElementById('task-create-form');
    if (createForm) {
        createForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            clearFieldErrors(createForm);

            const button = createForm.querySelector('button[type="submit"]');
            button.disabled = true;

            try {
                const response = await fetch(createForm.action, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: new FormData(createForm),
                    mode: 'same-origin',
                    credentials: 'same-origin'
                });
                const data = await readResponse(response);

                if (!response.ok) {
                    if (data.errors) {
                        showFieldErrors(data.errors);
                        throw new Error('Проверь правильность заполнения формы.');
                    }
                    throw new Error(data.error || data.message || 'Не удалось создать задание.');
                }

                const tbody = document.getElementById('task-table-body');
                const emptyRow = document.getElementById('empty-task-row');
                if (emptyRow) emptyRow.remove();
                tbody.insertAdjacentHTML('afterbegin', data.row_html);
                createForm.reset();
                applyTaskFilters();
                showToast(data.message);
            } catch (error) {
                const generalError = document.getElementById('task-form-error');
                if (generalError && !generalError.textContent) generalError.textContent = error.message;
                showToast(error.message || 'Не удалось связаться с сервером.', 'danger');
            } finally {
                button.disabled = false;
            }
        });

        createForm.addEventListener('input', function (event) {
            event.target.classList.remove('is-invalid');
            const error = createForm.querySelector(`[data-error-for="${event.target.name}"]`);
            if (error) error.textContent = '';
        });
    }

    // Изменение статуса на сервере.
    document.addEventListener('change', async function (event) {
        const select = event.target.closest('[data-status-select]');
        if (!select) return;

        const row = select.closest('[data-task-row]');
        const oldStatus = row.dataset.status;
        select.disabled = true;

        try {
            const response = await fetch(select.dataset.url, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
                body: JSON.stringify({status: select.value}),
                mode: 'same-origin',
                credentials: 'same-origin'
            });
            const data = await readResponse(response);
            if (!response.ok) throw new Error(data.error || 'Не удалось изменить статус.');

            row.dataset.status = data.status;
            const statusText = row.querySelector('.text-secondary.small');
            if (statusText) statusText.textContent = data.status_label;
            applyTaskFilters();
            showToast(data.message);
        } catch (error) {
            select.value = oldStatus;
            showToast(error.message || 'Ошибка соединения с сервером.', 'danger');
        } finally {
            select.disabled = false;
        }
    });

    // Удаление с подтверждением.
    document.addEventListener('click', async function (event) {
        const button = event.target.closest('[data-delete-task]');
        if (!button) return;

        if (!window.confirm(`Вы действительно хотите удалить задание «${button.dataset.title}»?`)) {
            return;
        }
        button.disabled = true;

        try {
            const response = await fetch(button.dataset.url, {
                method: 'POST',
                headers: {'X-CSRFToken': csrfToken},
                mode: 'same-origin',
                credentials: 'same-origin'
            });
            const data = await readResponse(response);
            if (!response.ok) throw new Error(data.error || 'Не удалось удалить задание.');

            const row = button.closest('[data-task-row]');
            if (row) row.remove();
            applyTaskFilters();
            showToast(data.message);
        } catch (error) {
            button.disabled = false;
            showToast(error.message || 'Ошибка соединения с сервером.', 'danger');
        }
    });
});
