# Третий клиент: JSON-источник фитнес-приложения

Проект реализует третий локальный источник данных для прототипа мультибазовой системы. Клиент имитирует фитнес-приложение или платформу носимого устройства, где профиль пользователя, активности, показатели здоровья и согласия хранятся внутри JSON-документа.

## Состав

- Django-проект с SQLite;
- модель `FitnessDocument` с `JSONField`;
- HTML-панель в едином стиле с остальными клиентами;
- формы ручного добавления JSON-документов, активностей, показателей и согласий;
- REST-эндпоинты для сервера-медиатора.

## Запуск

```bash
cd fitness_app_client_redesigned
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver 127.0.0.1:8003
```

### Linux / macOS

```bash
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver 127.0.0.1:8003
```

## HTML-страницы

```text
/             панель источника
/documents/   JSON-документы
/profiles/    профили пользователей
/activities/  активности
/metrics/     показатели здоровья
/consents/    согласия
```

## API

```text
/api/status/
/api/schema/
/api/documents/
/api/documents/<local_id>/
/api/users/
/api/users/<local_id>/
/api/activities/
/api/metrics/
/api/consents/
```

Примеры:

```bash
curl http://127.0.0.1:8003/api/status/
curl "http://127.0.0.1:8003/api/users/?open_to_offers=true&include_nested=true"
curl "http://127.0.0.1:8003/api/metrics/?metric_type=hrv&min_metric_value=50"
```

## Роль в прототипе

Клиент показывает документно-ориентированный вариант интеграции. Сервер-медиатор получает JSON-документы, выделяет вложенные сущности, применяет mapping и приводит данные к глобальной схеме вместе с данными первого и второго клиентов.
