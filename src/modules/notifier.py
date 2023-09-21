"""A module for detecting and notifying the user of dangerous in-game events."""

import time
import os
import cv2
import pygame
import threading
import numpy as np
import sys
import operator
import win32gui
import win32con
import win32com.client as client
import keyboard as kb
from enum import Enum

from src.routine.components import Point
from src.common import config, utils
from src.common.usb import USB
from src.common.common import Subject, Observer
from src.common.image_template import *
from src.common.bot_notification import *
from src.modules.capture import capture
from src.modules.chat_bot import chat_bot

class MineralType(Enum):
    HEART = 'heart mineral'
    CRYSTAL = 'crystal mineral'
    HERB_YELLOW = 'yellow herb'
    HERB_PURPLE = 'purple herb'
    
def exception_hook(exc_type, exc_value, tb):
    print('Traceback:')
    filename = tb.tb_frame.f_code.co_filename
    name = tb.tb_frame.f_code.co_name
    line_no = tb.tb_lineno
    info = (
        f"File {filename} line {line_no}, in {name}\n"
        f"{exc_type.__name__}, Message: {exc_value}\n"
    )
    notifier._notify(BotFatal.CRASH, info=info)

    print(f"File {filename} line {line_no}, in {name}")

    # Exception type 和 value
    print(f"{exc_type.__name__}, Message: {exc_value}")


sys.excepthook = exception_hook


class Notifier(Subject, Observer):
    ALERTS_DIR = os.path.join('assets', 'alerts')

    _default_notice_interval = 30

    def __init__(self):
        """Initializes this Notifier object's main thread."""
        super().__init__()
        pygame.mixer.init()
        self.mixer = pygame.mixer.music

        # sys.excepthook = exception_hook

        capture.attach(self)
        
        self.mineral_detect_time = 0

        self.player_pos_updated_time = 0
        self.player_pos = (0, 0)

        self.others_count = 0
        self.others_comming_time = 0
        self.others_detect_count = 0
        self.others_no_detect_count = 0

        self.rune_active_time = 0
        self.rune_alert_delay = 300         # 5 minutes

        self.mining_time = 0

        self.black_screen_threshold = 0.9
        self.white_room_threshold = 0.3

        self.notice_time_record = {}

        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """Starts this Notifier's thread."""

        print('\n[~] Started notifier')
        self.thread.start()

    def _main(self):
        self.ready = True
        while True:
            frame = capture.frame
            minimap = capture.minimap

            self.check_exception(frame)

            if config.enabled or config.change_channel:
                self.check_others(minimap)

            if config.enabled:
                self.check_alert(frame)
                self.check_rune_status(frame, minimap)
                self.check_minal(frame, minimap)
                self.check_skull(frame)
            time.sleep(0.05)

    def check_exception(self, frame):
        if frame is None:
            return
        height, width, _ = frame.shape
        if width < 400 and height < 400:
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Check for unexpected black screen
        if config.enabled and np.count_nonzero(gray < 15) / height / width > self.black_screen_threshold:
            self._notify(BotError.BLACK_SCREEN)

        # Check for white room
        if config.started_time and np.count_nonzero(gray == 255) / height / width >= self.white_room_threshold:
            self._notify(BotFatal.WHITE_ROOM)
        else:
            self.notice_time_record[BotFatal.WHITE_ROOM] = 0

        # Check for dead
        x = (frame.shape[1] - 450) // 2
        y = (frame.shape[0] - 200) // 2
        image = frame[y:y+200, x:x+450]
        tombstone = utils.multi_match(
            image, DEAD_TOBBSTONE_TEMPLATE, threshold=0.9)
        if tombstone:
            self._notify(BotError.DEAD)
            ok_btn = utils.multi_match(
                image, DEAD_OK_TEMPLATE, threshold=0.9)
            if ok_btn:
                USB().mouse_abs_move(capture.window['left'] + ok_btn[0][0] + x, capture.window['top'] + ok_btn[0][1] + y)
                time.sleep(1)
                USB().mouse_left_click()
                time.sleep(1)
                USB().mouse_left_click()
                
        # Check for no movement
        if config.enabled and operator.eq(config.player_pos, self.player_pos):
            interval = int(time.time() - self.player_pos_updated_time)
            if interval >= 30 and self.player_pos_updated_time:
                self._notify(BotError.NO_MOVEMENT, arg=interval,
                             info=f'duration:{interval}s')
        else:
            self.player_pos = config.player_pos
            self.player_pos_updated_time = time.time()

    def check_alert(self, frame):
        if frame is None:
            return

        x = (frame.shape[1] - 260) // 2
        y = (frame.shape[0] - 220) // 2
        ok_btn = utils.multi_match(
            frame[y:y+220, x:x+260], BUTTON_OK_TEMPLATE, threshold=0.9)

        x = (frame.shape[1] - 520) // 2
        y = (frame.shape[0] - 400) // 2
        end_talk = utils.multi_match(
            frame[y:y+400, x:x+520], END_TALK_TEMPLATE, threshold=0.9)
        if ok_btn or end_talk:
            USB().key_press('esc')
            time.sleep(0.1)

        # Check if window is forground
        if capture.hwnd and capture.hwnd != win32gui.GetForegroundWindow():
            try:
                shell = client.Dispatch("WScript.Shell")
                shell.SendKeys('%')
                if win32gui.IsIconic(capture.hwnd):
                    win32gui.SendMessage(
                        capture.hwnd, win32con.WM_SYSCOMMAND, win32con.SC_RESTORE, 0)
                win32gui.SetForegroundWindow(capture.hwnd)
            except Exception as e:
                print(e)
            time.sleep(0.5)

    def check_others(self, minimap):
        filtered = utils.filter_color(minimap, OTHER_RANGES)
        others = len(utils.multi_match(
            filtered, OTHER_TEMPLATE, threshold=0.7))

        guild_filtered = utils.filter_color(minimap, GUILDMATE_RANGES)
        guildmates = len(utils.multi_match(
            guild_filtered, GUILDMATE_TEMPLATE, threshold=0.7))

        others += guildmates

        config.stage_fright = others > 0

        self.others_count = others
        # print(f"others:{others} | others_detect_count:{self.others_detect_count} | others_no_detect_count:{self.others_no_detect_count}")
        if others > 0:
            self.others_detect_count += 1
            self.others_no_detect_count = 0
            if self.others_comming_time == 0:
                self.others_comming_time = time.time()
        else:
            self.others_no_detect_count += 1

        if self.others_no_detect_count == 150:
            self.others_no_detect_count += 1
            if self.others_comming_time > 0 and self.others_detect_count > 200:
                self.notifyOtherLeaved(others)
            self.others_detect_count = 0
            self.others_comming_time = 0
        elif self.others_detect_count == 1200:
            self.others_detect_count += 1
            self.othersLongStayWarnning(others)
        elif self.others_detect_count == 700:
            self.others_detect_count += 1
            self.othersStayWarnning2(others)
        elif self.others_detect_count == 400:
            self.others_detect_count += 1
            self.othersStayWarnning1(others)
        elif self.others_detect_count == 200:
            self.others_detect_count += 1
            self.notifyOtherComing(others)

    def check_rune_status(self, frame, minimap):
        if frame is None or minimap is None:
            config.rune_active = False
            self.rune_active_time = 0
            return

        now = time.time()
        filtered = utils.filter_color(minimap, RUNE_RANGES)
        matches = utils.multi_match(
            filtered, RUNE_TEMPLATE, threshold=0.9)
        # TODO rune buff bottom
        rune_buff = utils.multi_match(
            frame[:200, :], RUNE_BUFF_TEMPLATE, threshold=0.9)

        if not config.rune_active:
            if matches and config.routine.sequence and len(rune_buff) == 0:
                abs_rune_pos = (matches[0][0], matches[0][1])
                config.rune_pos = abs_rune_pos
                distances = list(
                    map(distance_to_rune, config.routine.sequence))
                index = np.argmin(distances)
                config.rune_closest_pos = config.routine[index].location
                config.rune_active = True
                if self.rune_active_time == 0:
                    self.rune_active_time = now
                    self._notify(BotInfo.RUNE_ACTIVE)
        elif len(rune_buff) > 1:
            config.rune_active = False
            self.rune_active_time = 0
        # Alert if rune hasn't been solved
        elif len(rune_buff) == 0 and now - self.rune_active_time > self.rune_alert_delay and self.rune_active_time != 0:
            self.notifyRuneError(now - self.rune_active_time)

    def check_minal(self, frame, minimap):
        if not config.mining_enable:
            return
        
        if frame is None or minimap is None:
            config.minal_active = False
            self.mining_time = 0
            return

        if config.minal_active:
            return

        if self.mineral_detect_time > 0 and time.time() - self.mineral_detect_time < 3:
            return
        
        self.mineral_detect_time = time.time()
        player_min = utils.multi_match(minimap, PLAYER_TEMPLATE, threshold=0.8)
        if len(player_min) == 0:
            return
        player_pos = player_min[0]

        matches = utils.multi_match(frame, MINAL_HEART_TEMPLATE)
        mineral_type = MineralType.HEART
        if len(matches) == 0:
            matches = utils.multi_match(frame, HERB_YELLOW_TEMPLATE)
            mineral_type = MineralType.HERB_YELLOW
        if len(matches) == 0:
            matches = utils.multi_match(frame, HERB_PURPLE_TEMPLATE)
            mineral_type = MineralType.HERB_PURPLE
        if len(matches) == 0:
            matches = utils.multi_match(frame, MINAL_CRYSTAL_TEMPLATE)
            mineral_type = MineralType.CRYSTAL
        if len(matches) > 0:
            self._notify(BotInfo.MINE_ACTIVE, info=mineral_type.value)
            player_template = PLAYER_SLLEE_TEMPLATE if config.command_book.name == 'shadower' else PLAYER_ISSL_TEMPLATE
            player = utils.multi_match(
                frame, player_template, threshold=0.9)
            if len(player) > 0:
                minal_full_pos = matches[0]
                if mineral_type == MineralType.HERB_YELLOW:
                    minal_full_pos = (minal_full_pos[0] - 16, minal_full_pos[1] - 70)
                elif mineral_type == MineralType.HERB_PURPLE:
                    minal_full_pos = (minal_full_pos[0] - 18, minal_full_pos[1] - 40)
                elif mineral_type == MineralType.CRYSTAL:
                    minal_full_pos = (minal_full_pos[0], minal_full_pos[1] - 50)
                elif mineral_type == MineralType.HEART:
                    minal_full_pos = (minal_full_pos[0], minal_full_pos[1] - 80)

                player_full_pos = player[0]
                dx_full = minal_full_pos[0] - player_full_pos[0]
                dy_full = minal_full_pos[1] - (player_full_pos[1] - 130)
                minal_pos = (
                    player_pos[0] + round(dx_full / 15.0), player_pos[1] + round(dy_full / 15.0))
                config.minal_pos = minal_pos
                distances = list(
                    map(distance_to_minal, config.routine.sequence))
                index = np.argmin(distances)
                config.minal_closest_pos = config.routine[index].location
                config.minal_active = True
    
    def check_skull(self, frame):
        player_template = PLAYER_SLLEE_TEMPLATE if config.command_book.name == 'shadower' else PLAYER_ISSL_TEMPLATE
        player = utils.multi_match(
                frame, player_template, threshold=0.9)
        if len(player) == 0:
            return
        player_pos = player[0]
        crop = frame[player_pos[1]-140:player_pos[1]-100, player_pos[0]+25:player_pos[0]+65]
        res = utils.multi_match(crop, SKULL_TEMPLATE)
        if len(res) > 0:
            self._notify(BotWarnning.BINDED)

            config.enabled = False
            while(len(res) > 0):
                for _ in range(4):
                    USB().key_press('left')
                    USB().key_press("right")
                res = utils.multi_match(crop, SKULL_TEMPLATE)
            config.enabled = True
            
    
    def _notify(self, event: Enum, arg=None, info: str = '') -> None:
        now = time.time()
        noticed_time = self.notice_time_record.get(event, 0)
        self.notify(event, min(noticed_time, now - noticed_time))

        if noticed_time == 0 or now - noticed_time >= config.default_notice_interval:
            self.notice_time_record[event] = now

            event_type = type(event)
            if event_type == BotFatal:
                self._alert('siren')
                time.sleep(20)
                chat_bot.voice_call()
                text = f'‼️[{event.value}] {info}'
                image_path = utils.save_screenshot(frame=capture.frame)
                self.send_message(text=text, image_path=image_path)
            elif event_type == BotError:
                if config.notice_level < 2:
                    return
                text = f'❗[{event.value}] {info}'
                image_path = utils.save_screenshot()
                self.send_message(text=text, image_path=image_path)
            elif event_type == BotWarnning:
                if config.notice_level < 3:
                    return
                text = f'⚠️[{event.value}] {info}'
                image_path = utils.save_screenshot(frame=capture.frame)
                self.send_message(text=text, image_path=image_path)
            elif event_type == BotInfo:
                if config.notice_level < 4:
                    return
                text = f'💡[{event.value}] {info}'
                self.send_message(text=text)
            elif event_type == BotDebug:
                if config.notice_level < 5:
                    return
                text = f'🔎[{event.value}] {info}'
                self.send_message(text=text)

    def othersLongStayWarnning(self, num):
        duration = int(time.time() - self.others_comming_time)
        text_notice = f"TP...duration:{duration}s, count:{num}"
        self._notify(BotError.OTHERS_STAY_OVER_120S,
                     arg=duration, info=text_notice)

    def othersStayWarnning1(self, num):
        duration = int(time.time() - self.others_comming_time)
        text_notice = f"duration:{duration}s, count:{num}"
        self._notify(BotWarnning.OTHERS_STAY_OVER_30S,
                     arg=duration, info=text_notice)

    def othersStayWarnning2(self, num):
        duration = int(time.time() - self.others_comming_time)
        text_notice = f"duration:{duration}s, count:{num}"
        self._notify(BotWarnning.OTHERS_STAY_OVER_60S,
                     arg=duration, info=text_notice)

    def notifyOtherComing(self, num):
        duration = int(time.time() - self.others_comming_time)
        text_notice = f"duration:{duration}s, count:{num}"
        self._notify(BotWarnning.OTHERS_COMMING,
                     arg=duration, info=text_notice)

    def notifyOtherLeaved(self, num):
        text_notice = f"count:{num}"
        self._notify(BotInfo.OTHERS_LEAVED, arg=num, info=text_notice)

    def notifyRuneResolved(self, rune_type):
        config.rune_active = False
        self.rune_active_time = 0
        self._notify(BotInfo.RUNE_LIBERATED, info=rune_type)

    def notifyRuneResolveFailed(self):
        duration = int(time.time() - self.rune_active_time)
        text_notice = f"{duration}s"
        self._notify(BotWarnning.RUNE_FAILED, arg=duration, info=text_notice)

    def notifyRuneError(self, time):
        text_notice = f"{int(time)}s"
        self._notify(BotError.RUNE_ERROR, arg=time, info=text_notice)

    def send_message(self, text=None, image=None, image_path=None):
        print(text)
        chat_bot.send_message(text=text, image=image, image_path=image_path)

    def _alert(self, name, volume=0.75):
        """
        Plays an alert to notify user of a dangerous event. Stops the alert
        once the key bound to 'Start/stop' is pressed.
        """
        config.enabled = False
        config.listener.enabled = False
        self.mixer.load(get_alert_path(name))
        self.mixer.set_volume(volume)
        self.mixer.play(-1)
        while not kb.is_pressed(config.listener.config['Start/stop']):
            time.sleep(0.1)
        self.mixer.stop()
        time.sleep(2)
        config.listener.enabled = True

    def _ping(self, name, volume=0.5):
        """A quick notification for non-dangerous events."""

        self.mixer.load(get_alert_path(name))
        self.mixer.set_volume(volume)
        self.mixer.play()

    def update(self, subject: Subject, *args, **kwargs) -> None:
        event = args[0]
        arg = args[1] if len(args) > 1 else None
        self._notify(event, arg)


notifier = Notifier()

#################################
#       Helper Functions        #
#################################


def get_alert_path(name):
    return os.path.join(Notifier.ALERTS_DIR, f'{name}.mp3')


def distance_to_rune(point):
    """
    Calculates the distance from POINT to the rune.
    :param point:   The position to check.
    :return:        The distance from POINT to the rune, infinity if it is not a Point object.
    """

    if isinstance(point, Point):
        return utils.distance(config.rune_pos, point.location)
    return float('inf')


def distance_to_minal(point):
    """
    Calculates the distance from POINT to the minal.
    :param point:   The position to check.
    :return:        The distance from POINT to the minal, infinity if it is not a Point object.
    """

    if isinstance(point, Point):
        return utils.distance(config.minal_pos, point.location)
    return float('inf')
