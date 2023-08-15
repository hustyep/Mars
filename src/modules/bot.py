"""An interpreter that reads and executes user-created routines."""

import threading
import time
import cv2
from os.path import splitext, basename
from src.common import config, utils
from src.detection import rune
from src.routine.routine import Routine
from src.command_book.command_book import CommandBook
from src.routine.components import Point
from src.common.vkeys import press, click, releaseAll
from src.common.interfaces import Configurable
import win32con
import win32clipboard as wc

# The rune's buff icon
RUNE_BUFF_TEMPLATE = cv2.imread('assets/rune_buff_template.jpg', 0)


class Bot(Configurable):
    """A class that interprets and executes user-defined routines."""

    DEFAULT_CONFIG = {
        'Interact': 'space',
        'Feed pet': 'L'
    }

    def __init__(self):
        """Loads a user-defined routine on start up and initializes this Bot's main thread."""

        super().__init__('keybindings')
        config.bot = self

        self.rune_active = False
        self.rune_pos = (0, 0)
        self.rune_closest_pos = (0, 0)      # Location of the Point closest to rune
        self.submodules = []
        self.command_book = None            # CommandBook instance
        self.stop_timer: threading.Timer = None

        config.routine = Routine()

        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """
        Starts this Bot object's thread.
        :return:    None
        """

        print('\n[~] Started main bot loop')
        self.thread.start()

    def _main(self):
        """
        The main body of Bot that executes the user's routine.
        :return:    None
        """

        self.ready = True
        config.listener.enabled = True
        last_fed = 0
        while True:
            if config.enabled and len(config.routine) > 0:
                # Buff and feed pets
                pet_settings = config.gui.settings.pets
                auto_feed = pet_settings.auto_feed.get()
                num_pets = pet_settings.num_pets.get()
                now = time.time()
                if auto_feed and now - last_fed > 600 / num_pets:
                    press(self.config['Feed pet'], 1)
                    last_fed = now
                
                self.command_book.buff.main()

                # Highlight the current Point
                config.gui.view.routine.select(config.routine.index)
                config.gui.view.details.display_info(config.routine.index)

                # Execute next Point in the routine
                element = config.routine[config.routine.index]
                if self.rune_active and isinstance(element, Point) \
                        and element.location == self.rune_closest_pos:
                    self._solve_rune()
                element.execute()
                config.routine.step()
            else:
                time.sleep(0.01)

    @utils.run_if_enabled
    def _solve_rune(self):
        """
        Moves to the position of the rune and solves the arrow-key puzzle.
        :param sct:     The mss instance object with which to take screenshots.
        :return:        None
        """

        move = self.command_book['move']
        move(*self.rune_pos).execute()
        adjust = self.command_book['adjust']
        adjust(*self.rune_pos).execute()
        time.sleep(0.5)
        press(self.config['Interact'], 1, down_time=0.2)        # Inherited from Configurable
        time.sleep(0.2)
        utils.save_screenshot(config.capture.frame)

        # if not rune.located_arrows(config.capture.frame):
        #     press(self.config['Interact'], 1, down_time=0.2)

        print('\nSolving rune:')
        inferences = []
        for _ in range(10):
            frame = config.capture.frame
            solution = rune.show_magic(frame)
            if solution is not None:
                print(', '.join(solution))
                if solution in inferences:
                    print('Solution found, entering result')
                    for arrow in solution:
                        press(arrow, 1, down_time=0.1)
                    break
                elif len(solution) == 4:
                    inferences.append(solution)
            time.sleep(0.1)
        threading.Timer(3, self.notify_rune_solved).start()

    def notify_rune_solved(self):
        self.rune_active = False

    def load_commands(self, file):
        try:
            self.command_book = CommandBook(file)
            config.gui.settings.update_class_bindings()
        except ValueError:
            pass    # TODO: UI warning popup, say check cmd for errors

    def cancel_rune_buff(self):
        for _ in range(3):
            time.sleep(0.3)
            frame = config.capture.frame
            rune_buff = utils.multi_match(frame[:frame.shape[0] // 8, :],
                                            RUNE_BUFF_TEMPLATE,
                                            threshold=0.9)
            if rune_buff:
                rune_buff_pos = min(rune_buff, key=lambda p: p[0])
                target = (
                    round(rune_buff_pos[0] + config.capture.window['left']),
                    round(rune_buff_pos[1] + config.capture.window['top'])
                )
                # click(target, button='left')
                # time.sleep(0.05)
                config.usb.mouse_relative_move(-35, 10)
                config.usb.mouse_relative_move(2, 5)
                time.sleep(0.05)
                click(target, button='right')
                time.sleep(0.03)
                click(target, button='right')
                time.sleep(0.03)
                click(target, button='right')
                
    def toggle(self, enabled: bool):
        config.bot.rune_active = False
        
        if enabled:
            config.capture.calibrated = False

        if config.enabled == enabled:
            return

        config.enabled = enabled
        utils.print_state()
        
        config.notifier.send_message(text=utils.bot_status())
        
        self.cancel_delay_stop()
        releaseAll()
        
        time.sleep(0.267)
       
        
    def delay_to_stop(self, delay: int = 3):
        if self.stop_timer:
            return
        
        self.stop_timer = threading.Timer(delay, self.toggle, (False, ))
        self.stop_timer.start()
        
    def cancel_delay_stop(self):
        if self.stop_timer is not None:
            self.stop_timer.cancel()
            self.stop_timer = None

        
    def setText(self, text):
        wc.OpenClipboard()
        wc.EmptyClipboard()
        wc.SetClipboardData(win32con.CF_UNICODETEXT, text)
        wc.CloseClipboard()
            
    def say(self, text):
        self.setText(text)
            
        config.usb.key_press('enter')
        time.sleep(0.1)
        config.usb.key_down('ctrl')
        config.usb.key_press("v")
        config.usb.key_up('ctrl')
        time.sleep(0.1)
        config.usb.key_press('enter')
        time.sleep(0.1)
        config.usb.key_press('enter')
        
    def say_to_all(self, text):
        self.toggle(False)
        time.sleep(1)
        self.say(text)
        self.toggle(True)
        
    def go_home(self):
        for i in range(0, 6):
            self.toggle(False)
            config.usb.key_press("H")
            time.sleep(0.5)
            config.usb.key_press("H")
            time.sleep(5)
