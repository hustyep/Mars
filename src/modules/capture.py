
import numpy as np
import win32gui
import time
import threading
import ctypes
import mss
import mss.windows
import operator
from src.common import config, utils
from src.common.image_template import *
from src.common.bot_notification import *
from src.common.common import Subject

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

class Capture(Subject):

    def __init__(self):
        super().__init__()
        self.frame = None
        self.minimap = None
        self.mm_tl = None
        self.mm_br = None
        self.minimap_sample = None
        self.sct = None
        self.hwnd = None
        self.window = {
            'left': 0,
            'top': 0,
            'width': 1366,
            'height': 768
        }
        self.calibrated = False

        self.lost_window_time = 0
        self.lost_minimap_time = 0
        self.lost_player_time = 0
        
        self.lost_time_threshold = 5
        
        self.ready = False
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
            if not self.calibrated:
                if not self.ready:
                    self.ready = True
                time.sleep(0.1)
                continue

            with mss.mss() as self.sct:
                while True:
                    if not self.calibrated:
                        break

                    self.locatePlayer()

                    if not self.ready:
                        self.ready = True
                    time.sleep(0.001)
        
    def start_auto_calibrate(self):
        # auto recalibrate
        
        timer = threading.Timer(3, self.start_auto_calibrate)
        timer.start()
        self.recalibrate(auto=True)

    def recalibrate(self, auto = False):
        # Calibrate screen capture
        self.hwnd = win32gui.FindWindow(None, "MapleStory")
        if (self.hwnd == 0):
            if config.enabled:
                now = time.time()
                if self.lost_window_time == 0:
                    self.lost_window_time = now
                self.notify(BotError.LOST_WINDOW, now - self.lost_window_time)
            return False
        
        self.lost_window_time = 0
        x1, y1, x2, y2 = win32gui.GetWindowRect(self.hwnd)  # 获取当前窗口大小
        
        self.window['left'] = x1
        self.window['top'] = y1
        self.window['width'] = x2 - x1
        self.window['height'] = y2 - y1

        # Calibrate by finding the top-left and bottom-right corners of the minimap
        with mss.mss() as sct:
            self.frame = self.screenshot(sct=sct)
        if self.frame is None:
            self.notify(BotDebug.SCREENSHOT_FAILED)
            return False
        
        tl = dll_helper.screenSearch(MM_TL_BMP, x1, y1, x2, y2)
        if tl:
            br= dll_helper.screenSearch(MM_BR_BMP,  x1, y1, x2, y2)

        if tl == None or br == None:
            if config.enabled:
                now = time.time()
                if self.lost_minimap_time == 0:
                    self.lost_minimap_time = now
                if now - self.lost_player_time >= self.lost_time_threshold:
                    self.notify(BotError.LOST_MINI_MAP, now - self.lost_minimap_time)
            return False
        
        mm_tl = (
            tl[0] - x1 - 2,
            tl[1] - y1 + 2
        )
        mm_br = (
            max(mm_tl[0] + PT_WIDTH, br[0] - x1 + 16),
            max(mm_tl[1] + PT_HEIGHT, br[1] - y1)
        )
        
        if operator.eq(mm_tl, self.mm_tl) and operator.eq(mm_br, self.mm_br):
            return True
        config.minimap_ratio = (mm_br[0] - mm_tl[0]) / (mm_br[1] - mm_tl[1])
        self.mm_tl = mm_tl
        self.mm_br = mm_br
        self.minimap_sample = self.frame[mm_tl[1]:mm_br[1], mm_tl[0]:mm_br[0]]
        
        self.lost_minimap_time = 0
        self.notify(BotDebug.CALIBRATED)
        
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
        # cv2.imshow("", minimap)
        # cv2.waitKey()
        # Determine the player's position
        player = utils.multi_match(minimap, PLAYER_TEMPLATE, threshold=0.8)
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
            self.lost_player_time = 0
            
            # Package display information to be polled by GUI
            self.minimap = minimap
            
            self.notify(BotDebug.PLAYER_LOCATION_UPDATE)
        elif config.enabled:
            now = time.time()
            if self.lost_player_time == 0:
                self.lost_player_time = now
            if now - self.lost_player_time >= self.lost_time_threshold:
                self.notify(BotError.LOST_PLAYER, now - self.lost_player_time)

    def screenshot(self, delay=1, sct=None):
        try:
            if sct is None:
                sct = self.sct
            return np.array(sct.grab(self.window))
        except mss.exception.ScreenShotError:
            print(f'\n[!] Error while taking screenshot, retrying in {delay} second'
                  + ('s' if delay != 1 else ''))
            time.sleep(delay)
        


capture = Capture()