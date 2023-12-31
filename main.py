import time
import platform 
import threading

from src.common.dll_loader import DllHelper
from src.modules.bot import Bot
from src.modules.capture import Capture
from src.modules.notifier import Notifier
from src.modules.listener import Listener
from src.modules.gui import GUI
from src.common import config

print(platform.architecture())
    
bot = Bot()
capture = Capture()
notifier = Notifier()
listener = Listener()
dll_helper = DllHelper()

dll_helper.start()
while not dll_helper.ready:
    time.sleep(0.01)

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

# threading.Timer(1, DllHelper.load).start()

gui = GUI()
gui.start()


#########################
##         Test        ##
#########################

# import cv2
# from src.common import utils
# RUNE_BUFF_TEMPLATE = cv2.imread('assets/rune_buff_template.jpg', 0)

# frame = cv2.imread("screenshot/new_player/maple_1691600971.png")
# minimap = capture.findMinimap(frame)
# cv2.imshow("minimap", minimap)
# notifier.checkOtherPlayer(minimap)

# frame = cv2.imread("screenshot/rune_solved/maple_1691652398.png")
# rune_buff = utils.multi_match(frame[:frame.shape[0] // 8, :], RUNE_BUFF_TEMPLATE, threshold=0.9)

# cv2.waitKey(0)
