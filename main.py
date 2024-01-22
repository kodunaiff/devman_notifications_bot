import argparse
import os

import requests
import telegram
from dotenv import load_dotenv


def create_chat_id():
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
    chat_id = args.chat_id
    return chat_id


def main():
    load_dotenv()
    token = os.environ['TOKEN_DVMN']
    token_tg = os.environ['TOKEN_TG']
    chat_id = create_chat_id()
    timestamp = 0
    bot = telegram.Bot(token=token_tg)

    url = 'https://dvmn.org/api/long_polling/'
    headers = {
        'Authorization': f'Token {token}',
    }
    while True:
        params = {
            'timestamp': timestamp,
        }
        try:
            response = requests.get(url, headers=headers, timeout=10, params=params)
            response.raise_for_status()
            answer = response.json()['new_attempts'][0]
            timestamp = answer['timestamp']
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
            print(f'нет изменений, последняя метка {timestamp}')
        except requests.exceptions.ConnectionError:
            (print('нет соединения'))


if __name__ == '__main__':
    main()
