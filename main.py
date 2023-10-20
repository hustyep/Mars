import time
import platform 

from src.common.dll_helper import dll_helper
from src.modules.bot import bot
from src.modules.capture import capture
from src.modules.notifier import notifier
from src.modules.detector import detector
from src.modules.listener import listener
from src.modules.gui import GUI
from src.modules.chat_bot import chat_bot
# from src.modules.chat_capture import chat_capture

print(platform.architecture())

dll_helper.start()
while not dll_helper.ready:
    time.sleep(0.01)

bot.start()
while not bot.ready:
    time.sleep(0.01)

capture.start()
while not capture.ready:
    time.sleep(0.01)
    
# chat_capture.start()
# while not chat_capture.ready:
#     time.sleep(0.01)

notifier.start()
while not notifier.ready:
    time.sleep(0.01)

detector.start()
while not detector.ready:
    time.sleep(0.01)

listener.start()
while not listener.ready:
    time.sleep(0.01)
    
chat_bot.start(command_handler=bot.on_new_command)
    
print('\n[~] Successfully initialized Mars')

gui = GUI()
gui.start()
