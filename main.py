import argparse
import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv


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
    timestamp = 0
    bot = telegram.Bot(token=token_tg)

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
                        bot.send_message(chat_id=chat_id,
                                         text=f'Здравствуйте, '
                                              f'преподаватель проверил работу! В работе "{lesson}" есть ошибки')
                    else:
                        bot.send_message(chat_id=chat_id,
                                         text=f'Здравствуйте, '
                                              f'преподаватель проверил работу! В работе "{lesson}" нет ошибок')

        except requests.exceptions.ReadTimeout:
            logging.warning(f'нет изменений, последняя метка {timestamp}')
        except requests.exceptions.ConnectionError:
            logging.warning('Отсутствие соединения, ожидание ..')
            time.sleep(20)


if __name__ == '__main__':
    main()
