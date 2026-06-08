from .base import BaseRestWrapper


class SportsSchoolWrapper(BaseRestWrapper):
    """Обёртка для второго клиента: спортивная школа с собственной локальной схемой."""

    def fetch_users(self):
        users = super().fetch_users()
        for user in users:
            user.setdefault("source_format", "legacy_school_schema")
        return users
