import requests

# from src.common import config
import aiohttp
import asyncio
import time

import telegram

telegram_apiToken = '6683915847:AAH1iOECS1y394jkvDCD2YhHLxIDIAmGGac'
telegram_chat_id = '805381440'

bot = telegram.Bot(telegram_apiToken)


# def send_text(message):
# apiURL = f'https://api.telegram.org/bot{config.telegram_apiToken}/sendMessage'
# try:
#     response = requests.post(apiURL, json={'chat_id': config.telegram_chat_id, 'text': message})
#     print(response.text)
# except Exception as e:
#     print(e)

# def send_photo(filePath):
#     apiURL = f'https://api.telegram.org/bot{config.telegram_apiToken}/sendPhoto'
#     params = {'chat_id': config.telegram_chat_id}
#     files = {'photo': open(filePath,'rb')}
#     resp = requests.post(apiURL, params, files=files)
#     return resp


def retry_on_error(func, wait=0.1, retry=0, *args, **kwargs):
    i = 0
    while True:
        try:
            return func(*args, **kwargs)
        # except telegram.error.NetworkError:
        except Exception as e:
            print(e)
            i += 1
            time.sleep(wait)
            if retry != 0 and i == retry:
                break


def send_text(message: str):
    retry_on_error(_send_text, retry=3, message=message)


def _send_text(message):
    asyncio.run(__send_text(message=message))


async def __send_text(message: str):
    async with bot:
        await bot.send_message(chat_id=telegram_chat_id, text=message)


def send_photo(filePath):
    try:
        asyncio.run(_send_photo(filePath))
    except Exception as e:
        print(e)


async def _send_photo(filePath: str):
    async with bot:
        await bot.send_photo(telegram_chat_id, photo=open(filePath, 'rb'))


# if __name__ == "__main__":
    # send_photo('C:\\Users\\Aaron\\Desktop\\MapleScreen\\btmRight.png')
    # send_text_retry("Hello from Python!")


# async def main():
#     bot_token = '6683915847:AAH1iOECS1y394jkvDCD2YhHLxIDIAmGGac'
#     chat_id = '805381440'
#     bot = telegram.Bot(bot_token)
#     async with bot:
#         await bot.send_message(text='Hi John!', chat_id=chat_id)
