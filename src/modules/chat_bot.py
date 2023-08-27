"""A module for sending message to telegram, wechat and email, also receiving command from telegram"""

import threading
from src.chat_bot.telegram_bot import TelegramBot
from src.chat_bot.wechat_bot import WechatBot
from src.common import config
    

class ChatBot():

    def __init__(self):
        self.command_handler = None
        self.wechat_bot = WechatBot(config.wechat_name)
        self.telegram_bot = TelegramBot(
            config.telegram_apiToken, config.telegram_chat_id, self.on_command)

        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self, command_handler):
        self.command_handler = command_handler
        print('\n[~] Started chat bot')
        self.thread.start()

    def _main(self):
        self.wechat_bot.run()
        self.telegram_bot.run()

    def send_text(self, text):
        self.telegram_bot.send_text(text)

    def send_image(self, image=None, image_path=None):
        self.telegram_bot.send_image(image, image_path)

    def send_message(self, text=None, image=None, image_path=None):
        self.telegram_bot.send_message(text=text, image_path=image_path)

    def voice_call(self):
        self.wechat_bot.voice_call()

    def video_call(self):
        self.wechat_bot.video_call()

    def on_command(self, command, *arg):
        return self.command_handler(command, *arg)
        
chat_bot = ChatBot()