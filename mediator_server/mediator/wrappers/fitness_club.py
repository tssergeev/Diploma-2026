from .base import BaseRestWrapper


class FitnessClubWrapper(BaseRestWrapper):
    """Обёртка для первого клиента: реляционная БД фитнес-клуба."""

    def fetch_users(self):
        users = super().fetch_users()
        for user in users:
            user.setdefault("source_format", "relational_fitness_club")
        return users
