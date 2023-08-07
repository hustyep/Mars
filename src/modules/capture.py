
import cv2
import numpy as np
import win32gui
import time
import threading
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

        self.ready = False
        self.calibrated = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """Starts this Capture's thread."""

        print('\n[~] Started video capture')
        self.thread.start()

    def _main(self):
        """Constantly monitors the player's position and in-game events."""

        # self.start_auto_calibrate()

        mss.windows.CAPTUREBLT = 0
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
        self.calibrated = False

        timer = threading.Timer(10, self.start_auto_calibrate)
        timer.start()

    def recalibrate(self):
        # Calibrate screen capture
        hwnd = win32gui.FindWindow(None, "MapleStory")
        if (hwnd == 0):
            # print("cant find maplestory")
            return False

        x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)  # 获取当前窗口大小
        self.window['left'] = x1
        self.window['top'] = y1
        self.window['width'] = x2 - x1
        self.window['height'] = y2 - y1

        # Calibrate by finding the top-left and bottom-right corners of the minimap
        with mss.mss() as self.sct:
            self.frame = self.screenshot()
        if self.frame is None:
            return False

        tl, _ = utils.single_match(self.frame, MM_TL_TEMPLATE)
        _, br = utils.single_match(self.frame, MM_BR_TEMPLATE)
        if tl == -1 or br == -1:
            # print("cant locate minimap")
            return False
        
        mm_tl = (
            tl[0] + MINIMAP_BOTTOM_BORDER,
            tl[1] + MINIMAP_TOP_BORDER
        )
        mm_br = (
            max(mm_tl[0] + PT_WIDTH, br[0] - MINIMAP_BOTTOM_BORDER),
            max(mm_tl[1] + PT_HEIGHT, br[1] - MINIMAP_BOTTOM_BORDER)
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
        player = utils.multi_match(
            minimap, PLAYER_TEMPLATE, threshold=0.8)
        if player:
            config.player_pos = utils.convert_to_relative(player[0], minimap)
        else:
            # print("cant locate player")
            pass

        # Package display information to be polled by GUI
        self.minimap = {
            'minimap': minimap,
            'rune_active': config.bot.rune_active,
            'rune_pos': config.bot.rune_pos,
            'path': config.path,
            'player_pos': config.player_pos
        }

    def screenshot(self, delay=1):
        try:
            return np.array(self.sct.grab(self.window))
        except mss.exception.ScreenShotError:
            print(f'\n[!] Error while taking screenshot, retrying in {delay} second'
                  + ('s' if delay != 1 else ''))
            time.sleep(delay)

    # def screen_shot(self, hwnd = None, picture_name = None):
    #     if hwnd is None:
    #         hwnd = win32gui.FindWindow(None, "MapleStory")
    #     hwndDC = win32gui.GetWindowDC(hwnd)  # 通过应用窗口句柄获得窗口DC
    #     x1, y1, x2, y2 = win32gui.GetWindowRect(hwnd)  # 获取当前窗口大小
    #     mfcDC = win32ui.CreateDCFromHandle(hwndDC)  # 通过hwndDC获得mfcDC(注意主窗口用的是win32gui库，操作位图截图是用win32ui库)
    #     cacheDC = mfcDC.CreateCompatibleDC()  # 创建兼容DC，实际在内存开辟空间（ 将位图BitBlt至屏幕缓冲区（内存），而不是将屏幕缓冲区替换成自己的位图。同时解决绘图闪烁等问题）
    #     savebitmap = win32ui.CreateBitmap()  # 创建位图
    #     width = x2 - x1
    #     height = y2 - y1
    #     savebitmap.CreateCompatibleBitmap(mfcDC, width, height)  # 设置位图的大小以及内容
    #     cacheDC.SelectObject(savebitmap)  # 将位图放置在兼容DC，即 将位图数据放置在刚开辟的内存里
    #     cacheDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)  # 截取位图部分，并将截图保存在剪贴板
    #     if picture_name is not None:
    #         savebitmap.SaveBitmapFile(cacheDC, picture_name)  # 将截图数据从剪贴板中取出，并保存为bmp图片
    #     img_buf = savebitmap.GetBitmapBits(True)

    #     img = np.frombuffer(img_buf, dtype="uint8")
    #     img.shape = (height, width, 4)

    #     cv2.imshow('shot', img)
    #     cv2.waitKey(0)

    #     # 释放内存
    #     win32gui.DeleteObject(savebitmap.GetHandle())
    #     cacheDC.DeleteDC()
    #     mfcDC.DeleteDC()
    #     win32gui.ReleaseDC(hwnd, hwndDC)
    #     return img


# if __name__ == '__main__':
#     capture = Capture()
#     img = capture.screenshot()
