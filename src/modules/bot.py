"""An interpreter that reads and executes user-created routines."""

import threading
import time
import cv2
import inspect
import importlib
import traceback
from os.path import splitext, basename
from src.common import config, utils, detection
from src.common.interfaces import Configurable
from src.command_book.command_book import CommandBook


# The rune's buff icon
RUNE_BUFF_TEMPLATE = cv2.imread('assets/rune_buff_template.jpg', 0)


class Bot(Configurable):
    """A class that interprets and executes user-defined routines."""

    DEFAULT_CONFIG = {
        'Interact': 'y',
        'Feed pet': '9'
    }

    def __init__(self):
        """Loads a user-defined routine on start up and initializes this Bot's main thread."""

        super().__init__('keybindings')
        config.bot = self

        self.rune_active = False
        self.rune_pos = (0, 0)
        # Location of the Point closest to rune
        self.rune_closest_pos = (0, 0)
        self.submodules = []
        self.command_book = None            # CommandBook instance
        # self.module_name = None
        # self.buff = components.Buff()

        # self.command_book = {}
        # for c in (components.Wait, components.Walk, components.Fall,
        #           components.Move, components.Adjust, components.Buff):
        #     self.command_book[c.__name__.lower()] = c

        # config.routine = Routine()

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

        # print('\n[~] Initializing detection algorithm:\n')
        # model = detection.load_model()
        # print('\n[~] Initialized detection algorithm')

        self.load_commands('./resources/command_books/shadower.py')
        self.ready = True
        config.listener.enabled = True
        last_fed = time.time()
        while True:
            if config.enabled:
                # Buff and feed pets
                time.sleep(5)
                
            else:
                time.sleep(10)

    @utils.run_if_enabled
    def _solve_rune(self, model):
        """
        Moves to the position of the rune and solves the arrow-key puzzle.
        :param model:   The TensorFlow model to classify with.
        :param sct:     The mss instance object with which to take screenshots.
        :return:        None
        """
        pass

    def load_commands(self, file):
        try:
            self.command_book = CommandBook(file)
            # config.gui.settings.update_class_bindings()
        except ValueError:
            pass
