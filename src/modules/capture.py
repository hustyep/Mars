
import cv2
import numpy as np
import win32gui
import time
import threading
from threading import Timer
import ctypes
import mss
import mss.windows
from src.common import config, utils

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

# The distance between the top of the minimap and the top of the screen
MINIMAP_TOP_BORDER = 5

# The thickness of the other three borders of the minimap
MINIMAP_BOTTOM_BORDER = 9

# Offset in pixels to adjust for windowed mode
WINDOWED_OFFSET_TOP = 36
WINDOWED_OFFSET_LEFT = 10

# The top-left and bottom-right corners of the minimap
MM_TL_TEMPLATE = cv2.imread('assets/minimap_tl_template.png', 0)
MM_BR_TEMPLATE = cv2.imread('assets/minimap_br_template.png', 0)

MMT_HEIGHT = max(MM_TL_TEMPLATE.shape[0], MM_BR_TEMPLATE.shape[0])
MMT_WIDTH = max(MM_TL_TEMPLATE.shape[1], MM_BR_TEMPLATE.shape[1])

# The player's symbol on the minimap
PLAYER_TEMPLATE = cv2.imread('assets/player_template.png', 0)
PT_HEIGHT, PT_WIDTH = PLAYER_TEMPLATE.shape

PLAYER_TEMPLATE_L = cv2.imread('assets/player_template_l.png', 0)

PLAYER_TEMPLATE_R = cv2.imread('assets/player_template_r.png', 0)


class Capture:

    def __init__(self):
        config.capture = self

        self.frame = None
        self.minimap = {}
        self.minimap_ratio = 1
        self.mm_tl = None
        self.mm_br = None
        self.minimap_sample = None
        self.sct = None
        self.window = {
            'left': 0,
            'top': 0,
            'width': 1366,
            'height': 768
        }

        self.lostPlayer = True
        self.ready = False
        self.calibrated = False
        self.stop_timer: Timer = None
        
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """Starts this Capture's thread."""

        print('\n[~] Started video capture')
        self.thread.start()

    def _main(self):
        """Constantly monitors the player's position and in-game events."""

        mss.windows.CAPTUREBLT = 0
        self.start_auto_calibrate()
        while True:
            self.calibrated = self.recalibrate()
            time.sleep(1)

            with mss.mss() as self.sct:
                while True:
                    if not self.calibrated:
                        if not self.ready:
                            self.ready = True
                        break

                    self.locatePlayer()

                    if not self.ready:
                        self.ready = True
                    time.sleep(0.001)
        
    def start_auto_calibrate(self):
        # auto recalibrate
        timer = threading.Timer(5, self.start_auto_calibrate)
        timer.start()
        self.recalibrate(auto=True)

    def recalibrate(self, auto = False):
        # Calibrate screen capture
        hwnd = win32gui.FindWindow(None, "MapleStory")
        if (hwnd == 0):
            notice = f"[!!!]cant find maplestory"
            config.notifier.send_text(notice)
            config.bot.toggle(False)
            return False

        x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)  # 获取当前窗口大小
        
        if auto and self.window['left'] == x1 and \
            self.window['top'] == y1 and \
            self.window['width'] == x2 - x1 and \
            self.window['height'] == y2 - y1 and \
            self.lostPlayer == False:
            return True
        
        self.window['left'] = x1
        self.window['top'] = y1
        self.window['width'] = x2 - x1
        self.window['height'] = y2 - y1

        # Calibrate by finding the top-left and bottom-right corners of the minimap
        with mss.mss() as sct:
            self.frame = self.screenshot(sct=sct)
        if self.frame is None:
            notice = f"[!!!]screenshot failed"
            config.notifier.send_text(notice)
            self.delay_to_stop()
            return False

        tl, _ = utils.single_match(self.frame, MM_TL_TEMPLATE)
        _, br = utils.single_match(self.frame, MM_BR_TEMPLATE)
        if tl == -1 and br == -1:
            notice = f"[!!!]cant locate minimap"
            config.notifier.send_text(notice)
            self.delay_to_stop()
            return False
        
        mm_tl = (
            tl[0] + MINIMAP_BOTTOM_BORDER,
            tl[1] + MINIMAP_TOP_BORDER
        )
        mm_br = (
            max(mm_tl[0] + PT_WIDTH, br[0] + 6),
            max(mm_tl[1] + PT_HEIGHT, br[1] - 25)
        )
        self.minimap_ratio = (mm_br[0] - mm_tl[0]) / (mm_br[1] - mm_tl[1])
        self.mm_tl = mm_tl
        self.mm_br = mm_br
        self.minimap_sample = self.frame[mm_tl[1]:mm_br[1], mm_tl[0]:mm_br[0]]
        
        utils.print_tag("recalibrate")
        print("window: ", self.window)
        print("mini_map:", mm_tl, mm_br)
        return True

    def locatePlayer(self):
        # Take screenshot
        self.frame = self.screenshot()
        if self.frame is None:
            return
        # Crop the frame to only show the minimap
        minimap = self.frame[self.mm_tl[1]:self.mm_br[1], self.mm_tl[0]:self.mm_br[0]]

        # Determine the player's position
        player = utils.multi_match( minimap, PLAYER_TEMPLATE, threshold=0.8)
        if len(player) == 0:
            player = utils.multi_match(minimap, PLAYER_TEMPLATE_R, threshold=0.8)
            if player:
                x = player[0][0] - 2
                y = player[0][1]
                player[0] = (x, y)
        if len(player) == 0:
            player = utils.multi_match(minimap, PLAYER_TEMPLATE_L, threshold=0.8)
            if player:
                x = player[0][0] + 2
                y = player[0][1]
                player[0] = (x, y)
        
        if player:
            # h, w, _ = minimap.shape
            # print(f"{player[0]} | {w}")
            config.player_pos = utils.convert_to_relative(player[0], minimap)
            self.lostPlayer = False
            if self.stop_timer:
                self.stop_timer.cancel()
                self.stop_timer = None
        elif config.enabled:
            notice = f"[!!!]cant locate player"
            print(notice)
            config.notifier.send_text(notice)
            self.lostPlayer = True
            self.delay_to_stop()

        # Package display information to be polled by GUI
        self.minimap = {
            'minimap': minimap,
            'rune_active': config.bot.rune_active,
            'rune_pos': config.bot.rune_pos,
            'path': config.path,
            'player_pos': config.player_pos
        }

    def screenshot(self, delay=1, sct=None):
        try:
            if sct is None:
                sct = self.sct
            return np.array(sct.grab(self.window))
        except mss.exception.ScreenShotError:
            print(f'\n[!] Error while taking screenshot, retrying in {delay} second'
                  + ('s' if delay != 1 else ''))
            time.sleep(delay)
            
    def findMinimap(self, frame):
        tl, _ = utils.single_match(frame, MM_TL_TEMPLATE)
        _, br = utils.single_match(frame, MM_BR_TEMPLATE)
        if tl == -1 or br == -1:
            # print("cant locate minimap")
            return None
        
        mm_tl = (
            tl[0] + MINIMAP_BOTTOM_BORDER,
            tl[1] + MINIMAP_TOP_BORDER
        )
        mm_br = (
            br[0] + 5,
            br[1] - 25
        )
        return frame[mm_tl[1]:mm_br[1], mm_tl[0]:mm_br[0]]
    
    def delay_to_stop(self, delay = 2):
        if self.stop_timer:
            return
        
        self.stop_timer = Timer(delay, config.bot.toggle, enabled = False)
        self.stop_timer.start()