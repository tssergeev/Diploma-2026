from urllib.parse import urljoin

import requests


class WrapperError(Exception):
    pass


class BaseRestWrapper:
    def __init__(self, source):
        self.source = source

    def make_url(self, endpoint):
        base = self.source.base_url.rstrip("/") + "/"
        return urljoin(base, endpoint.lstrip("/"))

    def get_json(self, endpoint, params=None):
        url = self.make_url(endpoint)
        try:
            response = requests.get(url, params=params or {}, timeout=self.source.timeout_seconds)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise WrapperError(f"Не удалось получить данные из {url}: {exc}") from exc
        except ValueError as exc:
            raise WrapperError(f"Источник {url} вернул не JSON") from exc

    def fetch_status(self):
        return self.get_json(self.source.status_endpoint)

    def fetch_schema(self):
        return self.get_json(self.source.schema_endpoint)

    def fetch_users(self):
        data = self.get_json(self.source.users_endpoint)
        if isinstance(data, dict):
            return data.get("results", [])
        if isinstance(data, list):
            return data
        raise WrapperError("Источник вернул неподдерживаемый формат списка пользователей")
