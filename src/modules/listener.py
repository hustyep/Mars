"""A keyboard listener to track user inputs."""

import time
import threading
import winsound
from pynput import keyboard
from datetime import datetime

from src.common.interfaces import Configurable
from src.common import config, utils


class Listener(Configurable):
    DEFAULT_CONFIG = {
        'Start/stop': 'f12',
        # 'Reload routine': 'f6',
        # 'Record position': 'f7'
    }
    BLOCK_DELAY = 1         # Delay after blocking restricted button press

    def __init__(self):
        """Initializes this Listener object's main thread."""

        super().__init__('controls')
        config.listener = self

        self.enabled = False
        self.ready = False
        self.block_time = 0
        # self.thread = threading.Thread(target=self._main)
        # self.thread.daemon = True
        self.kb_listener = keyboard.Listener(on_press=self.on_press,on_release=self.on_release)

    def on_press(self, key):
        if (not self.enabled):
            return
        
        try:
            print('alphanumeric key {0} pressed'.format(key.char))
        except AttributeError:
            print('special key {0} pressed'.format(key))
            if (key == keyboard.Key.f12):
                self.toggle_enabled()

    def on_release(self, key):
        print('{0} released'.format(key))
        
        if (not self.enabled):
            return
        if key == keyboard.Key.esc:
            # Stop listener
            pass
        elif key == keyboard.Key.print_screen:
            # config.capture.screenshot()
            pass


    def start(self):
        """
        Starts listening to user inputs.
        :return:    None
        """

        print('\n[~] Started keyboard listener')
        self.kb_listener.start()
        self.ready = True
        

    @staticmethod
    def toggle_enabled():
        """Resumes or pauses the current routine. Plays a sound to notify the user."""

        # config.bot.rune_active = False

        if not config.enabled:
            Listener.recalibrate_minimap()      # Recalibrate only when being enabled.

        config.enabled = not config.enabled
        utils.print_state()

        if config.enabled:
            winsound.Beep(784, 333)     # G5
        else:
            winsound.Beep(523, 333)     # C5
        time.sleep(0.267)

    @staticmethod
    def reload_routine():
        Listener.recalibrate_minimap()

        config.routine.load(config.routine.path)

        winsound.Beep(523, 200)     # C5
        winsound.Beep(659, 200)     # E5
        winsound.Beep(784, 200)     # G5

    @staticmethod
    def recalibrate_minimap():
        config.capture.calibrated = False
        while not config.capture.calibrated:
            time.sleep(0.01)
        # config.gui.edit.minimap.redraw()

    @staticmethod
    def record_position():
        pos = tuple('{:.3f}'.format(round(i, 3)) for i in config.player_pos)
        now = datetime.now().strftime('%I:%M:%S %p')
        config.gui.edit.record.add_entry(now, pos)
        print(f'\n[~] Recorded position ({pos[0]}, {pos[1]}) at {now}')
        time.sleep(0.6)
