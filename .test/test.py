import asyncio
import time
import telegram
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from usb import USB
import win32gui
import win32ui
import win32con
import win32api
import win32clipboard as wc
import cv2
import numpy as np

# from . import utils

class TelegramBot():
    def __init__(self, apiToken, chatID):
        self.apiTolen = apiToken
        self.chatID = chatID
        
        self.bot = telegram.Bot(apiToken)

    def _send_text(self, message):
        asyncio.run(self.__send_text(message=message))


    async def __send_text(self, message: str, chat_id=None):
        if chat_id is None:
            chat_id = self.chatID
        async with self.bot:
            await self.bot.send_message(chat_id=chat_id, text=message)
            
def setText(text):
    wc.OpenClipboard()
    wc.EmptyClipboard()
    wc.SetClipboardData(win32con.CF_UNICODETEXT, text)
    wc.CloseClipboard()
            
def say(text):
    usb = USB()
    usb.load()
    
    setText(text)
        
    usb.key_press('enter')
    time.sleep(0.1)
    usb.key_down('ctrl')
    usb.key_press("v")
    usb.key_up('ctrl')
    time.sleep(0.1)
    usb.key_press('enter')
    time.sleep(0.1)
    usb.key_press('enter')
    
def cancelBuff():
    usb = USB()
    usb.load()

def multi_match(frame, template, threshold=0.95):
    """
    Finds all matches in FRAME that are similar to TEMPLATE by at least THRESHOLD.
    :param frame:       The image in which to search.
    :param template:    The template to match with.
    :param threshold:   The minimum percentage of TEMPLATE that each result must match.
    :return:            An array of matches that exceed THRESHOLD.
    """

    if template.shape[0] > frame.shape[0] or template.shape[1] > frame.shape[1]:
        return []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if (template.ndim > 2):
        template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    locations = np.where(result >= threshold)
    locations = list(zip(*locations[::-1]))
    results = []
    src_copy = frame.copy()
    for p in locations:
        x = int(round(p[0] + template.shape[1] / 2))
        y = int(round(p[1] + template.shape[0] / 2))
        results.append((x, y))

        cv2.rectangle(src_copy, p, (p[0]+template.shape[1],
                      p[1]+template.shape[0]), (0, 0, 225), 2)
    cv2.imshow("result", src_copy)
    cv2.waitKey()
    return results

def filter_color(img, ranges):
    """
    Returns a filtered copy of IMG that only contains pixels within the given RANGES.
    on the HSV scale.
    :param img:     The image to filter.
    :param ranges:  A list of tuples, each of which is a pair upper and lower HSV bounds.
    :return:        A filtered copy of IMG.
    """
    if len(img) == 0:
        return None
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, ranges[0][0], ranges[0][1])
    for i in range(1, len(ranges)):
        mask = cv2.bitwise_or(mask, cv2.inRange(
            hsv, ranges[i][0], ranges[i][1]))

    # Mask the image
    color_mask = mask > 0
    result = np.zeros_like(img, np.uint8)
    result[color_mask] = img[color_mask]
    cv2.imshow("result", result)
    cv2.waitKey()
    return result
    usb.mouse_abs_move(1437, 300)
    usb.mouse_abs_move(2437, 400)
    usb.mouse_right_down()
    time.sleep(0.5)
    usb.mouse_right_up()
        
if __name__ == "__main__":
    # telegram_apiToken = '6497654972:AAExWRJvmuswPb2MzbtHi8fIp140TdeDSQM'
    # telegram_chat_id = '805381440'
    # send_text_retry("Hello from Python!")
    # bot = TelegramBot(telegram_apiToken, telegram_chat_id)
    # bot.send_photo('C:/Users/husty/Documents/Mars/screenshot/new_player/maple_1691724838.png')
    # bot.run()
    # bot._send_text("123")
    
    frame = cv2.imread(".test/Maple_230819_152709.png")
    
    # BIG_MOUSE_TEMPLATE = cv2.imread('assets/big_mouse_template.png', 0)
    # BIG_MOUSE_LEFT_TEMPLATE = cv2.imread('assets/big_mouse_left_template.png', 0)
    
    # GUILDMATE_RANGES = (
    #     ((120, 40, 180), (120, 110, 255)),
    # )
    # guildmate_filtered = filter_color(cv2.imread('assets/guildmate_template.png'), GUILDMATE_RANGES)
    # GUILDMATE_TEMPLATE = cv2.cvtColor(guildmate_filtered, cv2.COLOR_BGR2GRAY)
    # filted = filter_color(frame, GUILDMATE_RANGES)
    # guildmate = multi_match(filted, GUILDMATE_TEMPLATE, 0.7)
    
    big_mouse = cv2.imread('assets/big_mouse_template.png')
    hsv = cv2.cvtColor(big_mouse, cv2.COLOR_BGR2HSV)
    BIG_MOUSE_RANGES = (
        ((0, 180, 119), (4, 255, 187)),
        ((0, 255, 17), (0, 255, 153)),
    )
    BIG_MOUSE_TEMPLATE = filter_color(big_mouse, BIG_MOUSE_RANGES)
    filtered = filter_color(frame, BIG_MOUSE_RANGES)
    big_mouse = multi_match(filtered, BIG_MOUSE_TEMPLATE, threshold=0.7)
    if not big_mouse:
        big_mouse = multi_match(filtered, BIG_MOUSE_TEMPLATE, threshold=0.7)
    
    # say("hello1")
    cancelBuff()
