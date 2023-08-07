import time
import platform 
import threading

from src.common.dll_loader import DllLoader
from src.modules.bot import Bot
from src.modules.capture import Capture
from src.modules.notifier import Notifier
from src.modules.listener import Listener
from src.modules.gui import GUI
from src.common import config

def loadDefault():
    file_path = 'resources/command_books/shadower.py'
    config.bot.load_commands(file_path)

    routinepath = 'resources/routines/shadower/ResarchTrain1.csv'
    config.routine.load(routinepath)

print(platform.architecture())
    
bot = Bot()
capture = Capture()
notifier = Notifier()
listener = Listener()

bot.start()
while not bot.ready:
    time.sleep(0.01)

capture.start()
while not capture.ready:
    time.sleep(0.01)

notifier.start()
while not notifier.ready:
    time.sleep(0.01)

listener.start()
while not listener.ready:
    time.sleep(0.01)

print('\n[~] Successfully initialized Mars')

threading.Timer(1, DllLoader.load).start()

threading.Timer(3, loadDefault).start()

gui = GUI()
gui.start()