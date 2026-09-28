class ExternalServiceError(Exception):
    """Сервис недоступен или вернул некорректный ответ."""


class NotFoundError(Exception):
    """Город или валюта не найдены."""


class HTTPStatusError(ExternalServiceError):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"Внешний сервис вернул HTTP {status_code}")
