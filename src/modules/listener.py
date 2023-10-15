"""A keyboard listener to track user inputs."""

import time
import threading
import winsound
import keyboard as kb
from src.common.interfaces import Configurable
from src.common import config, utils
from datetime import datetime
from src.modules.capture import capture
from src.modules.notifier import notifier

class Listener(Configurable):
    DEFAULT_CONFIG = {
        'Start/stop': 'tab',
        'Reload routine': 'page up',
        'Record position': 'f12'
    }
    BLOCK_DELAY = 1         # Delay after blocking restricted button press

    def __init__(self):
        """Initializes this Listener object's main thread."""

        super().__init__('controls')
        config.listener = self

        self.enabled = False
        self.ready = False
        self.block_time = 0
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """
        Starts listening to user inputs.
        :return:    None
        """

        print('\n[~] Started keyboard listener')
        self.thread.start()

    def _main(self):
        """
        Constantly listens for user inputs and updates variables in config accordingly.
        :return:    None
        """

        self.ready = True
        while True:
            if self.enabled:
                if len(self.config['Start/stop']) > 0 and kb.is_pressed(self.config['Start/stop']):
                    Listener.toggle_enabled()
                elif len(self.config['Reload routine']) > 0 and kb.is_pressed(self.config['Reload routine']):
                    Listener.reload_routine()
                elif self.restricted_pressed('Record position'):
                    Listener.record_position()
            time.sleep(0.01)

    def restricted_pressed(self, action):
        """Returns whether the key bound to ACTION is pressed only if the bot is disabled."""

        if kb.is_pressed(self.config[action]):
            if not config.enabled:
                return True
            now = time.time()
            if now - self.block_time > Listener.BLOCK_DELAY:
                print(f"\n[!] Cannot use '{action}' while Mars is enabled")
                self.block_time = now
        return False

    @staticmethod
    def toggle_enabled():
        """Resumes or pauses the current routine. Plays a sound to notify the user."""

        config.rune_pos = None
        notifier.notice_time_record.clear()

        if not config.enabled:
            Listener.recalibrate_minimap()      # Recalibrate only when being enabled.
            config.started_time = time.time()
        else:
            config.started_time = None

        config.enabled = not config.enabled
        utils.print_state()

        # if config.enabled:
        #     winsound.Beep(784, 333)     # G5
        # else:
        #     winsound.Beep(523, 333)     # C5
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
        capture.calibrated = False
        # while not capture.calibrated:
        #     time.sleep(0.01)
        # config.gui.edit.minimap.redraw()

    @staticmethod
    def record_position():
        pos = config.player_pos
        now = datetime.now().strftime('%I:%M:%S %p')
        config.gui.edit.record.add_entry(now, pos)
        print(f'\n[~] Recorded position ({pos[0]}, {pos[1]}) at {now}')
        time.sleep(0.6)

listener = Listener()