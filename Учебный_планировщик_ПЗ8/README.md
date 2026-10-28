# Учебный планировщик — ПЗ № 8

Django + Django REST Framework. Для локальной разработки используется SQLite, для развёртывания на Render — PostgreSQL.

## Локальный запуск (Windows CMD)

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py test
python manage.py runserver
```

Откройте `http://127.0.0.1:8000/`. Для первого входа зарегистрируйте аккаунт: `/accounts/register/`.

## Основные страницы

- `/` — главная панель
- `/tasks/` — задания
- `/subjects/` — дисциплины
- `/api-console/` — интерфейс работы с API
- `/api/subjects/` — REST API дисциплин
- `/api/tasks/` — REST API заданий
- `/healthz/` — проверка доступности приложения, ожидаемый ответ `{"status":"ok"}`

Каждый пользователь работает только со своими дисциплинами и заданиями. API требует авторизацию. Для новых записей владелец назначается на сервере.

## Развёртывание на Render

1. Загрузите проект в новый GitHub-репозиторий. Не загружайте `.env`, `db.sqlite3`, пароли, токены или `SECRET_KEY`.
2. На Render создайте PostgreSQL-базу и Web Service из GitHub-репозитория. Желательно выбрать один регион для обоих сервисов.
3. Build Command: `bash build.sh` (установка зависимостей, миграции PostgreSQL и сбор статических файлов)
4. Start Command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
5. В Environment у Web Service добавьте:
   - `DJANGO_SECRET_KEY` — длинный случайный секрет;
   - `DJANGO_DEBUG` — `False`;
   - `DJANGO_ALLOWED_HOSTS` — домен сервиса, например `my-planner.onrender.com`, без `https://`;
   - `DJANGO_CSRF_TRUSTED_ORIGINS` — полный адрес, например `https://my-planner.onrender.com`;
   - `DATABASE_URL` — Internal Database URL из Render PostgreSQL.
6. `build.sh` автоматически выполняет `python manage.py migrate --noinput` и `collectstatic`. Убедитесь, что `DATABASE_URL` добавлен до запуска первого deploy, иначе миграции уйдут в локальную SQLite вместо PostgreSQL.
7. Проверьте `https://ВАШ-ДОМЕН/healthz/`, главную страницу, `/api/subjects/` и `/api/tasks/`. Войдите в аккаунт и проверьте создание/изменение записи через `/api-console/`.
8. Проверьте Logs в Render. Не публикуйте значения переменных окружения и полный `DATABASE_URL`.

## Что приложить в отчёт

Скриншоты: настройки переменных окружения без раскрытия значений секретов; успешный deploy/logs; открытая главная страница по HTTPS; ответ `/healthz/`; GET из API; создание или изменение записи; проверка, что запись сохранилась после обновления страницы. Зафиксируйте одну реальную ошибку из логов и её исправление, если такая ошибка возникла. Не придумывайте ошибку, которой не было.
