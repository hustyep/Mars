
import win32con
import win32clipboard as wc
import time
from random import random
from src.common import utils, config
from src.common.usb import USB
from src.common.image_template import *
from src.modules.capture import capture

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
    def click_key(key, delay = 0):
        USB().key_press(key)
        time.sleep(delay * (1 + 0.2 * random()))
    
    @staticmethod
    def press_key(key, delay = 0.05):
        USB().key_down(key)
        time.sleep(delay * (1 + 0.2 * random()))
        
    @staticmethod
    def release_key(key, delay = 0.05):
        USB().key_up(key)
        time.sleep(delay * (1 + 0.2 * random()))
    
    @staticmethod
    def cancel_rune_buff():
        rune_buff = None
        for _ in range(5):
            rune_buff = utils.multi_match(capture.frame[:200, :], RUNE_BUFF_TEMPLATE, threshold=0.9)
            if len(rune_buff) > 1:
                break
            time.sleep(0.5)

        if not rune_buff or len(rune_buff) < 2:
            return
        rune_buff_pos = min(rune_buff, key=lambda p: p[0])
        x = round(rune_buff_pos[0] + capture.window['left']) - 35
        y = round(rune_buff_pos[1] + capture.window['top']) + 10
        USB().mouse_abs_move(x, y)
        time.sleep(0.1)
        USB().mouse_right_down()
        time.sleep(0.3)
        USB().mouse_right_up()
        time.sleep(0.1)