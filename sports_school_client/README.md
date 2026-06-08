# Второй клиент: спортивная школа

Локальный Django-клиент, имитирующий источник данных спортивной школы для мультибазовой системы.

## Состав

- HTML-панель для просмотра и ручного добавления записей.
- REST API для сервера-медиатора.
- SQLite-база данных.
- Демонстрационные данные через management-команду.

## Основные сущности

- `School` — спортивная школа.
- `Section` — спортивная секция.
- `Student` — ученик.
- `AttendanceRecord` — запись посещаемости или занятия.
- `FitnessTest` — контрольные показатели.
- `DisclosurePermission` — разрешение на раскрытие данных и статус открытости.

## Запуск

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver 127.0.0.1:8002
```

Для Windows:

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver 127.0.0.1:8002
```

## Веб-панель

```text
http://127.0.0.1:8002/
```

## API

```text
http://127.0.0.1:8002/api/status/
http://127.0.0.1:8002/api/schema/
http://127.0.0.1:8002/api/schools/
http://127.0.0.1:8002/api/sections/
http://127.0.0.1:8002/api/students/
http://127.0.0.1:8002/api/attendance/
http://127.0.0.1:8002/api/fitness-tests/
http://127.0.0.1:8002/api/metrics/
http://127.0.0.1:8002/api/permissions/
http://127.0.0.1:8002/api/export/global/
```

## Примеры фильтрации

```text
http://127.0.0.1:8002/api/students/?open_to_offers=true
http://127.0.0.1:8002/api/students/?sport_type=swimming&min_attendance=3&period_days=90
http://127.0.0.1:8002/api/metrics/?metric_type=heart_rate_resting
```
