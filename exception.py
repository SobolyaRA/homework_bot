from email import message


class HTTPRequestError(Exception):
    def __init__(self, response):
        message = (
            f'Эндпоинт {response.url} недоступен'
            f'Код ответа: {response.status_code}'
        )
        super().__init__(message)


class ParseStatusError(Exception):
    def __init__(self, text):
        message = (
            f'Парсинг ответа : {text}'
        )
        super().__init__(message)


class CheckResponseError(Exception):
    def __init__(self, text):
        message = (
            f'Проверка ответа {text}'
        )
        super().__init__(message)