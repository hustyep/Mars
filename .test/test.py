import asyncio
import time
import telegram
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from usb import USB
import win32gui
import win32ui
import win32con
import win32api
import win32clipboard as wc

class TelegramBot():
    def __init__(self, apiToken, chatID):
        self.apiTolen = apiToken
        self.chatID = chatID
        
        self.bot = telegram.Bot(apiToken)

    def _send_text(self, message):
        asyncio.run(self.__send_text(message=message))


    async def __send_text(self, message: str, chat_id=None):
        if chat_id is None:
            chat_id = self.chatID
        async with self.bot:
            await self.bot.send_message(chat_id=chat_id, text=message)
            
def setText(text):
    wc.OpenClipboard()
    wc.EmptyClipboard()
    wc.SetClipboardData(win32con.CF_UNICODETEXT, text)
    wc.CloseClipboard()
            
def say(text):
    usb = USB()
    usb.load()
    
    setText(text)
        
    usb.key_press('enter')
    time.sleep(0.1)
    usb.key_down('ctrl')
    usb.key_press("v")
    usb.key_up('ctrl')
    time.sleep(0.1)
    usb.key_press('enter')
    time.sleep(0.1)
    usb.key_press('enter')

        
if __name__ == "__main__":
    # telegram_apiToken = '6497654972:AAExWRJvmuswPb2MzbtHi8fIp140TdeDSQM'
    # telegram_chat_id = '805381440'
    # send_text_retry("Hello from Python!")
    # bot = TelegramBot(telegram_apiToken, telegram_chat_id)
    # bot.send_photo('C:/Users/husty/Documents/Mars/screenshot/new_player/maple_1691724838.png')
    # bot.run()
    # bot._send_text("123")
    
    say("hello1")