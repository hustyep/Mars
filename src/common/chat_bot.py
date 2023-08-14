from src.common.telegram_bot import TelegramBot
from src.common.wechat_bot import WechatBot
from src.common import config, utils

class ChatBot():
    
    def __init__(self):
        self.wechat_bot = WechatBot(config.wechat_name)
        self.telegram_bot = TelegramBot(
                config.telegram_apiToken, config.telegram_chat_id)
    
    def run(self):
        self.wechat_bot.run()
        self.telegram_bot.run()
 
    def send_text(self, text):
        self.telegram_bot.send_text(text)
    
    def send_image(self, image=None, imagePath=None):
        self.telegram_bot.send_image(image, imagePath)
    
    def send_message(self, text=None, image=None, imagePath=None):
        self.telegram_bot.send_message(text, image, imagePath)
    
    def voice_call(self):
        self.wechat_bot.voice_call()
        
    def video_call(self):
        self.wechat_bot.video_call()