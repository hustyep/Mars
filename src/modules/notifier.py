"""A module for detecting and notifying the user of dangerous in-game events."""

import time
import os
import cv2
import pygame
import threading
import numpy as np
from src.routine.components import Point
from src.common import config, utils, mail
from src.common.telegram_bot import TelegramBot

RUNE_BUFF_TEMPLATE = cv2.imread('assets/rune_buff_template.jpg', 0)

# A rune's symbol on the minimap
RUNE_RANGES = (
    ((141, 148, 245), (146, 158, 255)),
)
rune_filtered = utils.filter_color(cv2.imread('assets/rune_template.png'), RUNE_RANGES)
RUNE_TEMPLATE = cv2.cvtColor(rune_filtered, cv2.COLOR_BGR2GRAY)

# Other players' symbols on the minimap
OTHER_RANGES = (
    ((0, 245, 215), (10, 255, 255)),
)
other_filtered = utils.filter_color(cv2.imread('assets/other_template.png'), OTHER_RANGES)
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
        
        self.prev_others = 0
        self.rune_start_time = 0

        self.room_change_threshold = 0.9
        self.rune_alert_delay = 90         # 3 minutes
        
        self.telegram_bot = TelegramBot(config.telegram_apiToken, config.telegram_chat_id)
        
        config.notifier = self

    def start(self):
        """Starts this Notifier's thread."""

        threading.Timer(1, self.telegram_bot.run).start()

        print('\n[~] Started notifier')
        self.thread.start()

    def _main(self):
        self.ready = True
        while True:
            if config.enabled:
                frame = config.capture.frame
                height, width, _ = frame.shape
                minimap = config.capture.minimap['minimap']

                # Check for unexpected black screen
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if np.count_nonzero(gray < 15) / height / width > self.room_change_threshold:
                    self._alert('siren')

                # # Check for elite warning
                # elite_frame = frame[height // 4:3 * height // 4, width // 4:3 * width // 4]
                # elite = utils.multi_match(elite_frame, ELITE_TEMPLATE, threshold=0.9)
                # if len(elite) > 0:
                #     self._alert('siren')

                # Check for other players entering the map
                self.checkOtherPlayer(minimap)

                # Check for rune
                now = time.time()
                if not config.bot.rune_active:
                    filtered = utils.filter_color(minimap, RUNE_RANGES)
                    matches = utils.multi_match(filtered, RUNE_TEMPLATE, threshold=0.9)
                    rune_buff = utils.multi_match(frame[:frame.shape[0] // 8, :], RUNE_BUFF_TEMPLATE, threshold=0.9)
                    if matches and config.routine.sequence and len(rune_buff) == 0:
                        abs_rune_pos = (matches[0][0], matches[0][1])
                        config.bot.rune_pos = utils.convert_to_relative(abs_rune_pos, minimap)
                        distances = list(map(distance_to_rune, config.routine.sequence))
                        index = np.argmin(distances)
                        config.bot.rune_closest_pos = config.routine[index].location
                        config.bot.rune_active = True
                        if self.rune_start_time == 0:
                            self.rune_start_time = now
                            self.notifyRuneAppeared()
                        else:
                            self.notifyRuneResolveFailed()
                    elif self.rune_start_time != 0:
                        if len(rune_buff) >= 1 or len(matches) == 0:
                            self.rune_start_time = 0
                            config.bot.rune_active = False
                            self.notifyRuneResolved()
                        else:
                            config.bot.rune_active = True
                            self.notifyRuneResolveFailed()
                elif now - self.rune_start_time > self.rune_alert_delay:     # Alert if rune hasn't been solved
                    # TODO 语音提醒
                    pass
            time.sleep(0.05)

    def checkOtherPlayer(self, minimap):
        filtered = utils.filter_color(minimap, OTHER_RANGES)
        others = len(utils.multi_match(filtered, OTHER_TEMPLATE, threshold=0.7))
        config.stage_fright = others > 0
        if others > self.prev_others:
            self.notifyPlayerComing(others)
        elif others < self.prev_others:
            self.notifyPlayerLeaved(others)
        self.prev_others = others            
            
    def notifyPlayerComing(self, num):        
        timestamp = int(time.time())
        imagePath = f"screenshot/new_player/maple_{timestamp}.webp"
        utils.save_screenshot(filename=imagePath)
        
        text_notice = f"有人来了，当前地图人数{num}"
        print(f"[!!!!]{text_notice}")
        if config.telegram_chat_id is not None:
            # self.telegram_bot.send_text(text_notice)
            self.telegram_bot.send_photo(imagePath, text_notice)
        elif config.mail_user is not None:
            mail.sendImage(text_notice, imagePath)
        
            
    def notifyPlayerLeaved(self, num):
        text_notice = f"[~]有人走了，当前地图人数{num}"
        self.send_text(text_notice)

            
    def notifyRuneAppeared(self):
        text_notice = f"[~]出现符文"
        self.send_text(text_notice)
            
    def notifyRuneResolved(self):
        timestamp = int(time.time())
        imagePath = f"screenshot/rune_solved/maple_{timestamp}.webp"
        utils.save_screenshot(filename=imagePath)

        text_notice = f"[~]解符文成功"
        print(f"[~]{text_notice}")
        if config.telegram_chat_id is not None:
            # self.telegram_bot.send_text(text_notice)
            self.telegram_bot.send_photo(imagePath, text_notice)
        elif config.mail_user is not None:
            mail.sendText(text_notice)
            
    def notifyRuneResolveFailed(self):
        timestamp = int(time.time())
        imagePath = f"screenshot/rune_failed/maple_{timestamp}.webp"
        utils.save_screenshot(filename=imagePath)
        
        text_notice = f"解符文失败, 已持续{time.time() - self.rune_start_time}s"
        print(f"[!!!!!!]{text_notice}")
        if config.telegram_chat_id is not None:
            # self.telegram_bot.send_text(text_notice)
            self.telegram_bot.send_photo(imagePath, text_notice)
        elif config.mail_user is not None:
            mail.sendText(text_notice)
            
    def send_text(self, text: str):
        print(text)
        if config.telegram_chat_id is not None:
            self.telegram_bot.send_text(text)
        elif config.mail_user is not None:
            mail.sendText(text)
                    
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
