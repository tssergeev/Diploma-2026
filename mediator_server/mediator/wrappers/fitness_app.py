from .base import BaseRestWrapper


class FitnessAppWrapper(BaseRestWrapper):
    """Обёртка для третьего клиента: JSON-документы фитнес-приложения."""

    def fetch_users(self):
        users = super().fetch_users()
        for user in users:
            user.setdefault("source_format", "document_json_source")
        return users
