# import requests

# import aiohttp
import cv2
import asyncio
import time
import telegram
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from src.common import utils, config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


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


class TelegramBot():
    def __init__(self, apiToken, chatID):
        self.apiTolen = apiToken
        self.chatID = chatID
        self.application = ApplicationBuilder().token(apiToken).build()
        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(CommandHandler('pause', self.pause))
        self.application.add_handler(
            CommandHandler('screenshot', self.screenshot))
        self.application.add_handler(CommandHandler('info', self.info))
        
        self.bot = telegram.Bot(apiToken)

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self.application.run_polling(
                read_timeout=60, write_timeout=60, pool_timeout=60, connect_timeout=60, timeout=60, close_loop=False)
        except Exception as e:
            print(e)
            time.sleep(0.5)
            self.run()

    def send_text(self, message: str):
        if not message:
            return
        retry_on_error(self._send_text, retry=3, message=message)

            
    def _send_text(self, message):
        asyncio.run(self.__send_text(message=message))

    async def __send_text(self, message: str, chat_id=None):
        if chat_id is None:
            chat_id = self.chatID
        async with self.bot:
            await self.bot.send_message(chat_id=chat_id, text=message)
            
    def send_message(self, text=None, image=None, imagePath=None):
        if image is None and imagePath is None:
            self.send_text(text)
            return
        
        try:
            asyncio.run(self._send_photo(imagePath, text))
        except Exception as e:
            print(e)

    def send_image(self, image=None, imagePath=None):
        try:
            asyncio.run(self._send_photo(imagePath))
        except Exception as e:
            print(e)
            try:
                asyncio.run(self._send_photo(imagePath))
            except Exception as e:
                print(e)


    async def _send_photo(self, filePath: str, message: str=None):
        async with self.bot:
                await self.bot.send_photo(self.chatID, photo=open(filePath, 'rb'), caption=message)
            
                
    async def replyText(self, update: Update, message: str):
        i = 0
        try:
            await update.effective_message.reply_text(message)
        except Exception as e:
            print(e)
            i += 1
            if i < 3:
                time.sleep(0.1)
                await update.effective_message.reply_text(message)

    async def replayPhoto(self, update: Update, photo_path: str, mesaage: str = None):
        i = 0
        try:
            await update.effective_message.reply_photo(photo=open(photo_path, 'rb'), caption=mesaage, connect_timeout=30)
        except Exception as e:
            print(e)
            i += 1
            if i < 3:
                time.sleep(0.1)
                await update.effective_message.reply_photo(photo=open(photo_path, 'rb'), caption=mesaage, connect_timeout=30)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        config.enabled = True
        config.bot.rune_active = False
        utils.print_state()
        await self.info(update=update, context=context)
        
        
    async def pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        config.enabled = False
        config.bot.rune_active = False
        utils.print_state()
        await self.info(update=update, context=context)


    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = utils.bot_status()
        await self.replyText(update, message)

    async def screenshot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        filepath = utils.save_screenshot()
        await self.replayPhoto(update, filepath, "screenshot")


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

if __name__ == "__main__":
    telegram_apiToken = '6683915847:AAH1iOECS1y394jkvDCD2YhHLxIDIAmGGac'
    telegram_chat_id = '805381440'
    # send_text_retry("Hello from Python!")
    bot = TelegramBot(telegram_apiToken, telegram_chat_id)
    bot.send_photo('C:/Users/husty/Documents/Mars/screenshot/new_player/maple_1691724838.png')
    # bot.run()
    # bot.send_text("123")


# async def main():
#     bot_token = '6683915847:AAH1iOECS1y394jkvDCD2YhHLxIDIAmGGac'
#     chat_id = '805381440'
#     bot = telegram.Bot(bot_token)
#     async with bot:
#         await bot.send_message(text='Hi John!', chat_id=chat_id)
