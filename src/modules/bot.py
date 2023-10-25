"""An interpreter that reads and executes user-created routines."""

import threading
import time
import random
from src.command_book.command_book import command_book
from src.chat_bot.chat_bot_entity import ChatBotCommand
from src.routine.routine import routine
from src.routine.components import Point
from src.common import config, utils
from src.common.action_simulator import ActionSimulator
from src.common.bot_notification import *
from src.common.vkeys import press, releaseAll
from src.common.interfaces import Configurable
from src.common.common import Observer, Subject
from src.modules.notifier import notifier
from src.modules.capture import capture
from src.modules.chat_bot import chat_bot
from src.modules.listener import listener
from src.modules.gui import gui

class Bot(Configurable, Observer):
    """A class that interprets and executes user-defined routines."""

    DEFAULT_CONFIG = {
        'Interact': 'space',
        'Feed pet': 'L',
        'Change channel': 'PageDn',
        'Attack': 'd'
    }

    def __init__(self):
        """Loads a user-defined routine on start up and initializes this Bot's main thread."""

        super().__init__('keybindings')
        config.global_keys = self.config
        notifier.attach(self)

        self.submodules = []

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
        listener.enabled = True
        last_fed = 0
        while True:
            if config.enabled and len(routine) > 0:
                # current element
                element = routine[routine.index]
                
                # Highlight the current Point
                gui.view.routine.select(routine.index)
                gui.view.details.display_info(routine.index)
                
                # feed pets
                pet_settings = gui.settings.pets
                auto_feed = pet_settings.auto_feed.get()
                num_pets = pet_settings.num_pets.get()
                now = time.time()
                if auto_feed and now - last_fed > 600 / num_pets:
                    press(self.config['Feed pet'], 1)
                    last_fed = now

                # Use Buff and Potion then move to the point
                if isinstance(element, Point):
                    # print(f"direction:{config.player_direction}, element: {element.location}, guard_point_l:{routine.guard_point_l}, guard_point_r:{routine.guard_point_r}")
                    command_book.potion.execute()
                    command_book.buff.execute()
                    
                    command_book.move(*element.location).execute()
                    if element.adjust:
                        command_book.adjust(*element.location).execute()

                # Execute next Point in the routine
                element.execute()
                
                # go next
                routine.step()
            else:
                time.sleep(0.01)
                

    def load_commands(self, file):
        try:
            command_book.load_commands(file)
            gui.settings.update_class_bindings()
        except ValueError:
            pass    # TODO: UI warning popup, say check cmd for errors

    def toggle(self, enabled: bool, reason: str = ''):
        config.rune_pos = None
        config.rune_closest_pos = None

        config.minal_active = False
        config.minal_pos = None
        config.minal_closest_pos = None

        if enabled:
            capture.calibrated = False

        if config.enabled == enabled:
            return

        config.enabled = enabled
        utils.print_state()

        if reason:
            notifier.send_message(self.bot_status(reason))

        releaseAll()

    def bot_status(self, ext='') -> str:
        message = (
            f"bot status: {'running' if config.enabled  else 'pause'}\n"
            f"rune status: {f'{time.time() - notifier.rune_active_time}s' if config.rune_pos is not None else 'clear'}\n"
            f"other players: {notifier.others_count}\n"
            f"reason: {ext}\n"
        )
        return message

    def on_new_command(self, command: ChatBotCommand, *args):
        match (command):
            case ChatBotCommand.INFO:
                return self.bot_status(), None
            case ChatBotCommand.START:
                self.toggle(True)
                return self.bot_status(), None
            case ChatBotCommand.PAUSE:
                self.toggle(False)
                return self.bot_status(), None
            case ChatBotCommand.SCREENSHOT:
                filepath = utils.save_screenshot(capture.frame)
                return None, filepath
            case ChatBotCommand.PRINTSCREEN:
                filepath = utils.save_screenshot()
                return None, filepath
            case ChatBotCommand.CLICK:
                ActionSimulator.click_key(args[0])
                filepath = utils.save_screenshot(capture.frame)
                return "done", filepath
            case ChatBotCommand.LEVEL:
                level = int(args[0])
                config.notice_level = level
                gui.settings.notification.notice_level.set(level)
                gui.settings.notification.notification_settings.save_config()
                return "done", None
            case ChatBotCommand.SAY:
                ActionSimulator.say_to_all(args[0])
                filepath = utils.save_screenshot(capture.frame)
                return f'said: "{args[0]}"', filepath
            case ChatBotCommand.TP:
                ActionSimulator.go_home()
                return "tp...", None
            case ChatBotCommand.CHANGE_CHANNEL:
                channel_num = 0
                if len(args) > 0:
                    channel_num = int(args[0])
                ActionSimulator.change_channel(channel_num)
                return "changing channel...", None

    def update(self, subject: Subject, *args, **kwargs) -> None:
        event_type = args[0]
        if len(args) > 1:
            arg = args[1]
        else:
            arg = 0
        if isinstance(event_type, BotFatal):
            self.toggle(False, event_type.value)
            chat_bot.voice_call()

        elif isinstance(event_type, BotError):
            chat_bot.voice_call()
            match (event_type):
                case BotError.OTHERS_STAY_OVER_120S:
                    ActionSimulator.go_home()
                case (_):
                    self.toggle(False, event_type.value)
            # end match
        elif isinstance(event_type, BotWarnning):
            match event_type:
                case BotWarnning.NO_MOVEMENT:
                    ActionSimulator.jump_down()
                case BotWarnning.OTHERS_STAY_OVER_30S:
                    words = ['cc plz', 'cc plz ', ' cc plz']
                    random_word = random.choice(words)
                    ActionSimulator.say_to_all(random_word)
                case BotWarnning.OTHERS_STAY_OVER_60S:
                    words = ['??', 'hello?', ' cc plz', 'bro?']
                    random_word = random.choice(words)
                    ActionSimulator.say_to_all(random_word)
                case BotWarnning.OTHERS_COMMING:
                    pass
        elif isinstance(event_type, BotInfo):
            match event_type:
                case BotInfo.BOSS_APPEAR:
                    threading.Timer(180, ActionSimulator.open_boss_box).start()
                case BotInfo.RUNE_ACTIVE:
                    pass
        elif isinstance(event_type, BotDebug):
            pass


bot = Bot()
