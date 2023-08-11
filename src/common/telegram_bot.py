import requests

# from src.common import config
import aiohttp
import asyncio
import time
import telegram
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

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


class TelegramBot:
    def __init__(self, apiToken, chatID):
        self.apiTolen = apiToken
        self.chatID = chatID
        self.application = ApplicationBuilder().token(apiToken).build()
        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(CommandHandler('pause', self.pause))
        self.application.add_handler(
            CommandHandler('screenshot', self.screenshot))
        self.application.add_handler(CommandHandler('info', self.info))

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
        retry_on_error(self._send_text, retry=3, message=message)

    def _send_text(self, message):
        asyncio.run(self.__send_text(message=message))

    async def __send_text(self, message: str, chat_id=None):
        if chat_id is None:
            chat_id = self.chatID

        await self.application.bot.send_message(chat_id=chat_id, text=message)

    def send_photo(self, filePath):
        try:
            asyncio.run(self._send_photo(filePath))
        except Exception as e:
            print(e)

    async def _send_photo(self, filePath: str):
        async with self.bot:
            await self.bot.send_photo(self.chatID, photo=open(filePath, 'rb'))

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

    async def replayPhoto(self, update: Update, photo: open):
        i = 0
        try:
            await update.effective_message.reply_photo(photo=photo)
        except Exception as e:
            print(e)
            i += 1
            if i < 3:
                time.sleep(0.1)
                await update.effective_message.reply_photo(photo=photo)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = "start"
        await self.replyText(update, text)
        
    async def pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = "pause"
        await self.replyText(update, text)

    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = (
            f"bot status: {'running' if False else 'pause'}\n"
            f"other players: {0}"
        )
        await self.replyText(update, message)

    async def screenshot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        photo = open(
            'C:/Users/Aaron/Documents/Python/Mars/screenshot/rune_solved/maple_1691651660.png', 'rb')
        await self.replayPhoto(update, photo)


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
    # send_photo('C:\\Users\\Aaron\\Desktop\\MapleScreen\\btmRight.png')
    # send_text_retry("Hello from Python!")
    bot = TelegramBot(telegram_apiToken, telegram_chat_id)
    bot.run()
    # bot.send_text("123")


# async def main():
#     bot_token = '6683915847:AAH1iOECS1y394jkvDCD2YhHLxIDIAmGGac'
#     chat_id = '805381440'
#     bot = telegram.Bot(bot_token)
#     async with bot:
#         await bot.send_message(text='Hi John!', chat_id=chat_id)
