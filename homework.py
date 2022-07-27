import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exception import CheckResponseError, HTTPRequestError, ParseStatusError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot: telegram.Bot, message: str):
    """Отправка сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        message = f'Сбой при отправке сообщения {error}'
        raise Exception(message)
    else:
        logging.info(f'Бот отправил сообщение {message} в Telegram')


def get_api_answer(current_timestamp):
    """Создание и отправка запроса к эндпоинту."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    logging.info(f'Отправка запроса на {ENDPOINT} с параметрами {params}')
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        raise HTTPRequestError
    return response.json()


def check_response(response):
    """Проверка корректности ответа."""
    if not response:
        message = 'Пустой словарь'
        raise KeyError(message)

    if not isinstance(response, dict):
        message = 'Некорректный тип'
        raise TypeError(message)

    if 'homeworks' not in response:
        message = 'Не найден ожидаемый ключ в ответе'
        raise KeyError(message)

    if not isinstance(response.get('homeworks'), list):
        message = 'Несоответствие формата ответа'
        raise CheckResponseError(message)

    return response['homeworks']


def parse_status(homework):
    """Проверка статуса конкретной дз."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        message = 'Отсутствует имя домашней работы'
        raise KeyError(message)

    homework_status = homework.get('status')
    if 'status' not in homework:
        message = 'Отсутствует ключ'
        raise ParseStatusError(message)

    verdict = HOMEWORK_STATUSES.get(homework_status)
    if homework_status not in HOMEWORK_STATUSES:
        message = 'Статус домашней работы неизвестен'
        raise KeyError(message)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка доступности переменных окружения."""
    list_env = [
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID
    ]
    return all(list_env)


def main():
    """Основная логика работы бота."""
    finaly_send = {
        'error': None
    }
    if not check_tokens():
        logging.critical(
            'Отсутствует обязательная переменная окружения.'
        )
        message = 'Программа принудительно остановлена.'
        sys.exit(message)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            homework = homeworks[0]
            message = parse_status(homework)
            if finaly_send.get(homework['homework_name']) != message:
                send_message(bot, message)
                finaly_send[homework['homework_name']] = message
            current_timestamp = response.get('current_date')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if finaly_send['error'] != message:
                send_message(bot, message)
                finaly_send['error'] = message
        else:
            finaly_send['error'] = None
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s -- %(lineno)s  -- %(levelname)s -- %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)])
    main()
