# import requests

# import aiohttp
import asyncio
import time
import telegram
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from src.chat_bot.chat_bot_entity import ChatBotEntity, ChatBotCommand

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.FATAL
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


class TelegramBot(ChatBotEntity):
    def __init__(self, apiToken, chatID, command_handler):
        self.apiTolen = apiToken
        self.chatID = chatID
        self.command_handler = command_handler

        # commands = ['start', 'pause', 'screenshot', 'info', 'buff', 'say', 'tp']
        self.application = ApplicationBuilder().token(apiToken).build()
        for command in ChatBotCommand:
            self.application.add_handler(CommandHandler(command.value, self.on_command))

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

    def send_text(self, message: str, retry=3):
        if not message:
            return
        retry_on_error(self._send_text, retry=retry, message=message)

    def _send_text(self, message):
        asyncio.run(self.__send_text(message=message))

    async def __send_text(self, message: str, chat_id=None):
        if chat_id is None:
            chat_id = self.chatID
        async with self.bot:
            await self.bot.send_message(chat_id=chat_id, text=message)

    def send_image(self, image_path, caption=None, retry=3):
        retry_on_error(self._send_image, retry=retry, image_path=image_path, caption=caption)

    def _send_image(self, image_path, caption=None):
        asyncio.run(self.__send_image(image_path, caption))

    async def __send_image(self, image_path: str, caption: str = None):
        async with self.bot:
            await self.bot.send_photo(self.chatID, photo=open(image_path, 'rb'), caption=caption)
            
    def send_message(self, text=None, image_path=None, retry=3):
        if image_path is None:
            self.send_text(text, retry=retry)
            return

        self.send_image(image_path, caption=text, retry=retry)

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
        
    async def on_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.effective_message.text
        list = text.split(" ")
        command = list[0][1:]
        args = context.args
        message, image_path = self.command_handler(ChatBotCommand(command), *args)
        if image_path:
            await self.replayPhoto(update, image_path, message)
        else:
            await self.replyText(update, message)


if __name__ == "__main__":
    telegram_apiToken = '6683915847:AAH1iOECS1y394jkvDCD2YhHLxIDIAmGGac'
    telegram_chat_id = '805381440'
    # send_text_retry("Hello from Python!")
    bot = TelegramBot(telegram_apiToken, telegram_chat_id)
    bot.send_photo(
        'C:/Users/husty/Documents/Mars/screenshot/new_player/maple_1691724838.png')
    # bot.run()
    # bot.send_text("123")


# async def main():
#     bot_token = '6683915847:AAH1iOECS1y394jkvDCD2YhHLxIDIAmGGac'
#     chat_id = '805381440'
#     bot = telegram.Bot(bot_token)
#     async with bot:
#         await bot.send_message(text='Hi John!', chat_id=chat_id)

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