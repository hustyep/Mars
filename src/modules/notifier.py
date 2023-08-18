"""A module for detecting and notifying the user of dangerous in-game events."""

import time
import os
import cv2
import pygame
import threading
import numpy as np
from random import random
from src.routine.components import Point
from src.common import config, utils
from src.common.chat_bot import ChatBot

RUNE_BUFF_TEMPLATE = cv2.imread('assets/rune_buff_template.jpg', 0)
BUTTON_OK_TEMPLATE = cv2.imread('assets/btn_ok_template.png', 0)
END_TALK_TEMPLATE = cv2.imread('assets/end_talk_template.png', 0)

# A rune's symbol on the minimap
RUNE_RANGES = (
    ((141, 148, 245), (146, 158, 255)),
)
rune_filtered = utils.filter_color(
    cv2.imread('assets/rune_template.png'), RUNE_RANGES)
RUNE_TEMPLATE = cv2.cvtColor(rune_filtered, cv2.COLOR_BGR2GRAY)

# Other players' symbols on the minimap
OTHER_RANGES = (
    ((0, 245, 215), (10, 255, 255)),
)
other_filtered = utils.filter_color(cv2.imread(
    'assets/other_template.png'), OTHER_RANGES)
OTHER_TEMPLATE = cv2.cvtColor(other_filtered, cv2.COLOR_BGR2GRAY)

# The Elite Boss's warning sign
# ELITE_TEMPLATE = cv2.imread('assets/elite_template.jpg', 0)


def get_alert_path(name):
    return os.path.join(Notifier.ALERTS_DIR, f'{name}.mp3')


class Notifier:
    ALERTS_DIR = os.path.join('assets', 'alerts')

    def __init__(self):
        """Initializes this Notifier object's main thread."""

        pygame.mixer.init()
        self.mixer = pygame.mixer.music

        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

        self.cur_others = 0
        self.other_comming_time = 0
        self.detect_count = 0
        self.no_detect_count = 0
        
        self.rune_start_time = 0
        self.noticed_white_room = False
        self.noticed_black_screen = False

        self.room_change_threshold = 0.9
        self.white_room_threshold = 0.2
        self.rune_alert_delay = 90         # 3 minutes

        self.chat_bot = ChatBot()

        config.notifier = self

    def start(self):
        """Starts this Notifier's thread."""

        threading.Timer(3, self.chat_bot.run).start()

        print('\n[~] Started notifier')
        self.thread.start()

    def _main(self):
        self.ready = True
        while True:                        
            if config.enabled:
                frame = config.capture.frame
                minimap = config.capture.minimap['minimap']

                self.exceptionCheck(frame)
                
                self.checkOtherPlayer(minimap)
                
                self.checkAlert(frame)

                # Check for rune
                now = time.time()
                if not config.bot.rune_active:
                    filtered = utils.filter_color(minimap, RUNE_RANGES)
                    matches = utils.multi_match(
                        filtered, RUNE_TEMPLATE, threshold=0.9)
                    rune_buff = utils.multi_match(
                        frame[:frame.shape[0] // 8, :], RUNE_BUFF_TEMPLATE, threshold=0.9)
                    if matches and config.routine.sequence and len(rune_buff) == 0:
                        abs_rune_pos = (matches[0][0], matches[0][1])
                        config.bot.rune_pos = utils.convert_to_relative(
                            abs_rune_pos, minimap)
                        distances = list(
                            map(distance_to_rune, config.routine.sequence))
                        index = np.argmin(distances)
                        config.bot.rune_closest_pos = config.routine[index].location
                        config.bot.rune_active = True
                        if self.rune_start_time == 0:
                            self.rune_start_time = now
                            self.notifyRuneAppeared()
                        else:
                            self.notifyRuneResolveFailed()
                    elif self.rune_start_time != 0:
                        if len(rune_buff) > 1 and len(matches) == 0:
                            self.rune_start_time = 0
                            self.notifyRuneResolved()
                        else:
                            config.bot.rune_active = True
                            self.notifyRuneResolveFailed()
                elif now - self.rune_start_time > self.rune_alert_delay:     # Alert if rune hasn't been solved
                    self.notifyRuneError()
            time.sleep(0.05)

    def exceptionCheck(self, frame):
        if frame is None:
            return 
        height, width, _ = frame.shape
        if width < 400 and height < 400:
            return
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Check for unexpected black screen
        if np.count_nonzero(gray < 15) / height / width > self.room_change_threshold:
            if not self.noticed_black_screen:
                config.bot.delay_to_stop(5)
                self.send_message('[!!!]black screen')
                self.noticed_black_screen = True
        else:
            self.noticed_black_screen = False            

        # Check for white room
        white_radio = np.count_nonzero(gray == 255) / height / width
        if white_radio >= self.white_room_threshold and config.capture.lost_player_time > 0:
            if not self.noticed_white_room:
                self.noticed_white_room = True  
                config.bot.toggle(False)
                self.chat_bot.voice_call()
                for i in range(3):
                    self.send_message('[!!!!!!!!!!]white home')
                    time.sleep(0.2)
        else:
            self.noticed_white_room = False
            
        # # Check for elite warning
        # elite_frame = frame[height // 4:3 * height // 4, width // 4:3 * width // 4]
        # elite = utils.multi_match(elite_frame, ELITE_TEMPLATE, threshold=0.9)
        # if len(elite) > 0:
        #     self._alert('siren')

        # Check for other players entering the map

    def checkAlert(self, frame):
        x = (frame.shape[1] - 260) // 2
        y = (frame.shape[0] - 100) // 2
        ok_btn = utils.multi_match(frame[y:y+100, x:x+260], BUTTON_OK_TEMPLATE, threshold=0.9)
        if ok_btn:
            config.usb.key_press('esc')
            
        x = (frame.shape[1] - 520) // 2
        y = (frame.shape[0] - 190) // 2
        end_talk = utils.multi_match(frame[y:y+190, x:x+520], END_TALK_TEMPLATE, threshold=0.9)
        if end_talk:
            config.usb.key_press('esc')

    def checkOtherPlayer(self, minimap):
        filtered = utils.filter_color(minimap, OTHER_RANGES)
        others = len(utils.multi_match(
            filtered, OTHER_TEMPLATE, threshold=0.7))
        config.stage_fright = others > 0
        
        self.cur_others = others
        # print(f"others:{others} | detect_count:{self.detect_count} | no_detect_count:{self.no_detect_count}")
        if others > 0:
            self.detect_count += 1
            self.no_detect_count = 0
            if self.other_comming_time == 0:
                self.other_comming_time = time.time()
        else:
            self.no_detect_count += 1
        
        if self.no_detect_count == 150:
            self.no_detect_count += 1
            if self.other_comming_time > 0 and self.detect_count > 200:
                self.notifyOtherLeaved(others)
            self.detect_count = 0
            self.other_comming_time = 0
        elif self.detect_count == 700:
            self.detect_count += 1
            self.othersLongStayWarnning(others)
        elif self.detect_count == 400:
            self.detect_count += 1
            self.othersStayWarnning(others)
        elif self.detect_count == 200:
            self.detect_count += 1
            self.notifyOtherComing(others)


    def othersLongStayWarnning(self, num):
        timestamp = int(time.time())
        imagePath = f"screenshot/new_player/maple_{timestamp}.webp"
        utils.save_screenshot(filename=imagePath)
        
        text_notice = f"[!!!]回城。。。有人已停留{int(time.time() - self.other_comming_time)}s, 当前地图人数{num}"
        self.send_message(text=text_notice,
                        image=config.capture.frame, imagePath=imagePath)
        config.bot.go_home()        
        
            
    def othersStayWarnning(self, num):
        str = 'cc pls'
        if random() >= 0.7:
            str = 'cc pls '
        elif random() >= 0.4:
            str = ' cc pls'
        config.bot.say_to_all(str)
        
        timestamp = int(time.time())
        imagePath = f"screenshot/new_player/maple_{timestamp}.webp"
        utils.save_screenshot(filename=imagePath)
        
        text_notice = f"[!!!]有人已停留{int(time.time() - self.other_comming_time)}s, 当前地图人数{num}"
        self.send_message(text=text_notice,
                        image=config.capture.frame, imagePath=imagePath)
            

    def notifyOtherComing(self, num):
        self.noticed_other_short_stay = True
        timestamp = int(time.time())
        imagePath = f"screenshot/new_player/maple_{timestamp}.webp"
        utils.save_screenshot(filename=imagePath)

        text_notice = f"[!!!]有人来了, 已停留{int(time.time() - self.other_comming_time)}s, 当前地图人数{num}"
        self.send_message(text=text_notice,
                        image=config.capture.frame, imagePath=imagePath)

    def notifyOtherLeaved(self, num):
        text_notice = f"[~]有人走了，当前地图人数{num}"
        self.send_message(text=text_notice)

    def notifyRuneAppeared(self):
        text_notice = f"[~]出现符文"
        self.send_message(text=text_notice)

    def notifyRuneResolved(self):
        timestamp = int(time.time())
        imagePath = f"screenshot/rune_solved/maple_{timestamp}.webp"
        utils.save_screenshot(filename=imagePath)

        text_notice = f"[~]解符文成功"
        print(f"[~]{text_notice}")
        self.send_message(text=text_notice,
                          image=config.capture.frame, imagePath=imagePath)

    def notifyRuneResolveFailed(self):
        timestamp = int(time.time())
        imagePath = f"screenshot/rune_failed/maple_{timestamp}.webp"
        utils.save_screenshot(filename=imagePath)

        text_notice = f"[!]解符文失败, 已持续{int(time.time() - self.rune_start_time)}s"
        self.send_message(text=text_notice,
                          image=config.capture.frame, imagePath=imagePath)
        
    def notifyRuneError(self):
        pass

    def send_message(self, text=None, image=None, imagePath=None):
        print(text)
        self.chat_bot.send_message(text, image=image, imagePath=imagePath)

    def _alert(self, name, volume=0.75):
        """
        Plays an alert to notify user of a dangerous event. Stops the alert
        once the key bound to 'Start/stop' is pressed.
        """
        pass
        # config.enabled = False
        # config.listener.enabled = False
        # self.mixer.load(get_alert_path(name))
        # self.mixer.set_volume(volume)
        # self.mixer.play(-1)
        # while not kb.is_pressed(config.listener.config['Start/stop']):
        #     time.sleep(0.1)
        # self.mixer.stop()
        # time.sleep(2)
        # config.listener.enabled = True

    def _ping(self, name, volume=0.5):
        """A quick notification for non-dangerous events."""

        self.mixer.load(get_alert_path(name))
        self.mixer.set_volume(volume)
        self.mixer.play()


#################################
#       Helper Functions        #
#################################
def distance_to_rune(point):
    """
    Calculates the distance from POINT to the rune.
    :param point:   The position to check.
    :return:        The distance from POINT to the rune, infinity if it is not a Point object.
    """

    if isinstance(point, Point):
        return utils.distance(config.bot.rune_pos, point.location)
    return float('inf')
