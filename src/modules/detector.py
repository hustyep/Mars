"""A module for detecting and notifying the user of dangerous in-game events."""

import time
import threading
import numpy as np
from enum import Enum

from src.routine.components import Point
from src.common import config, utils, settings
from src.common.usb import USB
from src.common.image_template import *
from src.common.bot_notification import *
from src.modules.capture import capture
from src.modules.notifier import notifier


class MineralType(Enum):
    HEART = 'heart mineral'
    CRYSTAL = 'crystal mineral'
    HERB_YELLOW = 'yellow herb'
    HERB_PURPLE = 'purple herb'


class Detector():

    def __init__(self):
        """Initializes this Detector object's main thread."""
        super().__init__()

        self.player_pos_min = None
        self.player_pos = None

        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """Starts this Detector's thread."""

        print('\n[~] Started detector')
        self.thread.start()

    def _main(self):
        self.ready = True
        while True:
            frame = capture.frame
            minimap = capture.minimap

            if config.enabled and frame is not None and minimap is not None:
                self.check_mineral(frame, minimap)
                self.check_skull(frame)
                self.check_dead(frame)
            time.sleep(0.2)
        

    def check_mineral(self, frame, minimap):
        if not config.mining_enable:
            return

        if frame is None or minimap is None:
            config.minal_active = False
            self.mining_time = 0
            return

        if config.minal_active:
            return

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
            notifier._notify(BotInfo.MINE_ACTIVE, info=mineral_type.value)
            player_template = config.routine.role_template
            player = utils.multi_match(
                frame, player_template, threshold=0.9)
            if len(player) > 0:
                config.mineral_type = mineral_type
                minal_full_pos = matches[0]
                if mineral_type == MineralType.HERB_YELLOW:
                    minal_full_pos = (
                        minal_full_pos[0] - 18, minal_full_pos[1] - 70)
                elif mineral_type == MineralType.HERB_PURPLE:
                    minal_full_pos = (
                        minal_full_pos[0] - 18, minal_full_pos[1] - 40)
                elif mineral_type == MineralType.CRYSTAL:
                    minal_full_pos = (
                        minal_full_pos[0], minal_full_pos[1] - 50)
                elif mineral_type == MineralType.HEART:
                    minal_full_pos = (
                        minal_full_pos[0] - 10, minal_full_pos[1] - 80)

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
        player_template = config.routine.role_template
        player = utils.multi_match(
            frame, player_template, threshold=0.9)
        if len(player) == 0:
            return
        player_pos = player[0]
        crop = frame[player_pos[1]-140:player_pos[1] -
                     100, player_pos[0]+25:player_pos[0]+65]
        res = utils.multi_match(crop, SKULL_TEMPLATE)
        if len(res) > 0:
            notifier._notify(BotWarnning.BINDED)

            config.enabled = False
            while (len(res) > 0):
                for _ in range(4):
                    USB().key_press('left')
                    USB().key_press("right")
                if capture.frame is None:
                    break
                crop = capture.frame[player_pos[1]-140:player_pos[1] -
                                     100, player_pos[0]+25:player_pos[0]+65]
                res = utils.multi_match(crop, SKULL_TEMPLATE)
            config.enabled = True

    # Check for dead
    def check_dead(self, frame):
        x = (frame.shape[1] - 450) // 2
        y = (frame.shape[0] - 200) // 2
        image = frame[y:y+200, x:x+450]
        tombstone = utils.multi_match(
            image, DEAD_TOBBSTONE_TEMPLATE, threshold=0.9)
        if tombstone:
            notifier._notify(BotError.DEAD)
            ok_btn = utils.multi_match(
                image, DEAD_OK_TEMPLATE, threshold=0.9)
            if ok_btn:
                USB().mouse_abs_move(capture.window['left'] + ok_btn[0][0] + x,
                                     capture.window['top'] + ok_btn[0][1] + y)
                time.sleep(1)
                USB().mouse_left_click()
                time.sleep(1)
                USB().mouse_left_click()


detector = Detector()

#################################
#       Helper Functions        #
#################################


def distance_to_minal(point):
    """
    Calculates the distance from POINT to the minal.
    :param point:   The position to check.
    :return:        The distance from POINT to the minal, infinity if it is not a Point object.
    """

    if isinstance(point, Point):
        return utils.distance(config.minal_pos, point.location)
    return float('inf')
