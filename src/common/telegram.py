import requests
import cv2
import time
from src.common import config


def send_text(message):
    apiURL = f'https://api.telegram.org/bot{config.telegram_apiToken}/sendMessage'
    try:
        response = requests.post(apiURL, json={'chat_id': config.telegram_chat_id, 'text': message})
        print(response.text)
    except Exception as e:
        print(e)
        
def send_photo(filePath):
    apiURL = f'https://api.telegram.org/bot{config.telegram_apiToken}/sendPhoto'
    params = {'chat_id': config.telegram_chat_id}
    files = {'photo': open(filePath,'rb')}
    resp = requests.post(apiURL, params, files=files)
    return resp

if __name__ == "__main__":
    send_photo('C:\\Users\\Aaron\\Desktop\\MapleScreen\\btmRight.png')
    # send_text("Hello from Python!")


# async def main():
#     bot_token = '6683915847:AAH1iOECS1y394jkvDCD2YhHLxIDIAmGGac'
#     chat_id = '805381440'
#     bot = telegram.Bot(bot_token)
#     async with bot:
#         await bot.send_message(text='Hi John!', chat_id=chat_id)