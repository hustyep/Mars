import time
import platform 

from src.common.usb import USB
from src.common.dll_loader import DllLoader
from src.modules.bot import Bot
from src.modules.capture import Capture
from src.modules.listener import Listener

print(platform.architecture())

usb = USB()
usb.load()

dllLoader = DllLoader()
    
bot = Bot()
capture = Capture()
# notifier = Notifier()
listener = Listener()

bot.start()
while not bot.ready:
    time.sleep(0.01)

capture.start()
while not capture.ready:
    time.sleep(0.01)
    
listener.start()
while not listener.ready:
    time.sleep(0.01)