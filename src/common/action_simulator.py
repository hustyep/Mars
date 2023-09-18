
import win32con
import win32clipboard as wc
import time
from random import random
from src.common import utils, config
from src.common.usb import USB
from src.common.image_template import *
from src.modules.capture import capture
import threading


class ActionSimulator:

    @staticmethod
    def setText(text):
        wc.OpenClipboard()
        wc.EmptyClipboard()
        wc.SetClipboardData(win32con.CF_UNICODETEXT, text)
        wc.CloseClipboard()

    @staticmethod
    def say(text):
        ActionSimulator.setText(text)
        ActionSimulator.click_key('enter', 0.3)
        ActionSimulator.press_key("ctrl", 0.05)
        ActionSimulator.click_key("v", 0.05)
        ActionSimulator.release_key("ctrl", 0.3)
        ActionSimulator.click_key('enter', 0.3)
        ActionSimulator.click_key('enter', 0.05)

    @staticmethod
    def say_to_all(text):
        last_status = config.enabled
        config.enabled = False
        time.sleep(1)
        ActionSimulator.say(text)
        if last_status:
            config.enabled = True

    @staticmethod
    def go_home():
        for i in range(0, 6):
            config.enabled = False
        ActionSimulator.click_key('H', 0.5)
        ActionSimulator.click_key('H', 5)

    @staticmethod
    def stop_game():
        config.enabled = False

        ActionSimulator.press_key('alt', 0.5)
        ActionSimulator.click_key('f4', 0.5)
        ActionSimulator.release_key('alt', 0.5)
        ActionSimulator.click_key('enter', 10)
        USB().consumer_sleep()

    @staticmethod
    def potion_buff():
        USB().key_press('0')
        time.sleep(0.5)
        USB().key_press('-')

    @staticmethod
    def click_key(key, delay=0):
        USB().key_press(key)
        time.sleep(delay * (1 + 0.2 * random()))

    @staticmethod
    def press_key(key, delay=0.05):
        USB().key_down(key)
        time.sleep(delay * (1 + 0.2 * random()))

    @staticmethod
    def release_key(key, delay=0.05):
        USB().key_up(key)
        time.sleep(delay * (1 + 0.2 * random()))
        
    @staticmethod
    def mouse_left_click(position=None, delay=0.05):
        if position:
            USB().mouse_abs_move(position[0], position[1])
            time.sleep(0.5)

        USB().mouse_left_click()
        time.sleep(delay * (1 + 0.2 * random()))
        
    @staticmethod
    def cancel_rune_buff():
        config.enabled = False
        for _ in range(5):
            rune_buff = utils.multi_match(
                capture.frame[:200, :], RUNE_BUFF_TEMPLATE, threshold=0.9)
            if len(rune_buff) <= 2:
                break
            
            rune_buff_pos = min(rune_buff, key=lambda p: p[0])
            x = round(rune_buff_pos[0] + capture.window['left']) + 10
            y = round(rune_buff_pos[1] + capture.window['top']) + 10
            USB().mouse_abs_move(x, y)
            time.sleep(0.06)
            USB().mouse_right_down()
            time.sleep(0.2)
            USB().mouse_right_up()
            time.sleep(0.2)
        config.enabled = True

    @staticmethod
    def go_to_msroom(num: int):
        ActionSimulator.click_key('f8')

        ActionSimulator.change_channel(num=num, enable=False)

    @staticmethod
    def change_channel(num: int = 0, enable=True):
        config.enabled = False
        config.change_channel = True
        config.rune_active = False
        config.rune_pos = None
        config.rune_closest_pos = None
        threading.Timer(5, ActionSimulator._change_channel, (num, enable, )).start()

    @staticmethod
    def _change_channel(num: int = 0, enable=True) -> None:
        key_settings = config.global_keys
        change_key = key_settings['Change channel']

        ActionSimulator.click_key(change_key)

        if num > 0:
            item_width = 50
            item_height = 40
            channel_1 = (0, 0)

            row = (num - 1) // 10
            col = (num - 1) % 10

            x = channel_1[0] + col * item_width
            y = channel_1[1] + row * item_height
            USB().mouse_abs_move(x, y)
            USB().mouse_left_click()
        else:
            ActionSimulator.click_key('down')
            ActionSimulator.click_key('right')
            ActionSimulator.click_key('enter')

        while capture.frame is None:
            time.sleep(0.1)
        frame = capture.frame
        x = (frame.shape[1] - 260) // 2
        y = (frame.shape[0] - 220) // 2
        ok_btn = utils.multi_match(
            frame[y:y+220, x:x+260], BUTTON_OK_TEMPLATE, threshold=0.9)
        if ok_btn:
            ActionSimulator.click_key('enter')
            ActionSimulator._change_channel()
            return

        delay = 0
        while not config.lost_minimap:
            delay += 0.1
            if delay > 5:
                ActionSimulator._change_channel()
                return
            time.sleep(0.1)

        while config.lost_minimap:
            time.sleep(0.1)

        if not enable:
            return

        config.enabled = True

        others = False
        for i in range(5):
            if config.stage_fright:
                others = True
                break
            time.sleep(1)

        if others:
            ActionSimulator.change_channel()
        else:
            config.change_channel = False
            config.enabled = True
