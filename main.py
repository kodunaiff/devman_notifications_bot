import argparse
import logging
import os
import time

import requests
from dotenv import load_dotenv
from telegram.ext import Updater

logger = logging.getLogger(__name__)


class TelegramLogsHandler(logging.Handler):
    def __init__(self, tg_bot, chat_id):
        super().__init__()
        self.chat_id = chat_id
        self.tg_bot = tg_bot

    def emit(self, record):
        log_entry = self.format(record)
        self.tg_bot.send_message(chat_id=self.chat_id, text=log_entry)


def fetch_chat_id():
    parser = argparse.ArgumentParser(
        description='Скрипт для отслеживания, выполненных заданий'
    )
    parser.add_argument(
        '-c',
        '--chat_id',
        help='введите свой чат-айди ТГ',
        type=int,
        default=os.environ['CHAT_ID']
    )

    args = parser.parse_args()
    return args.chat_id


def get_statistic(token, timestamp):
    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {token}',
    }
    params = {
        'timestamp': timestamp,
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def main():
    load_dotenv()

    token = os.environ['TOKEN_DVMN']
    token_tg = os.environ['TOKEN_TG']
    chat_id = fetch_chat_id()

    updater = Updater(token=token_tg)
    dp = updater.dispatcher

    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(dp.bot, chat_id))
    logger.info("Бот запущен!")

    timestamp = 0

    while True:
        try:
            response = get_statistic(token, timestamp)
            if response['status'] == 'timeout':
                timestamp = response['timestamp_to_request']
            if response['status'] == 'found':
                timestamp = response['last_attempt_timestamp']
                for answer in response['new_attempts']:
                    status = answer['is_negative']
                    lesson = answer['lesson_title']
                    if status:
                        dp.bot.send_message(chat_id=chat_id,
                                            text=f'Здравствуйте, '
                                                 f'преподаватель проверил работу! В работе "{lesson}" есть ошибки')
                    else:
                        dp.bot.send_message(chat_id=chat_id,
                                            text=f'Здравствуйте, '
                                                 f'преподаватель проверил работу! В работе "{lesson}" нет ошибок')

        except requests.exceptions.ReadTimeout:
            logger.debug(f'нет изменений, последняя метка {timestamp}')
        except requests.exceptions.ConnectionError:
            logger.debug('Отсутствие соединения, ожидание ..')
            time.sleep(20)
        except Exception as err:
            logger.exception(err)
            time.sleep(5)


if __name__ == '__main__':
    main()
