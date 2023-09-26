"""An interpreter that reads and executes user-created routines."""

import threading
import time
import random
from src.command_book.command_book import CommandBook
from src.chat_bot.chat_bot_entity import ChatBotCommand
from src.detection import rune
from src.routine.routine import Routine
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
from src.modules.detector import MineralType
from src.common.image_template import *


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
                # feed pets
                pet_settings = config.gui.settings.pets
                auto_feed = pet_settings.auto_feed.get()
                num_pets = pet_settings.num_pets.get()
                now = time.time()
                if auto_feed and now - last_fed > 600 / num_pets:
                    press(self.config['Feed pet'], 1)
                    last_fed = now

                # Buff
                config.command_book.buff.main()

                # Potion
                config.command_book.potion.main()

                # Highlight the current Point
                config.gui.view.routine.select(config.routine.index)
                config.gui.view.details.display_info(config.routine.index)

                # Execute next Point in the routine
                element = config.routine[config.routine.index]
                if config.rune_active and isinstance(element, Point) \
                        and element.location == config.rune_closest_pos:
                    self._solve_rune()
                elif config.minal_active and isinstance(element, Point) \
                        and element.location == config.minal_closest_pos:
                    self._mining()

                element.execute()
                config.routine.step()
            else:
                time.sleep(0.01)

    @utils.run_if_enabled
    def _solve_rune(self, retry=True):
        """
        Moves to the position of the rune and solves the arrow-key puzzle.
        :param sct:     The mss instance object with which to take screenshots.
        :return:        None
        """

        move = config.command_book['move']
        move(*config.rune_pos).execute()
        adjust = config.command_book['adjust']
        adjust(*config.rune_pos).execute()
        adjustx = config.command_book['adjustx']
        adjustx(*config.rune_pos).execute()
        time.sleep(0.5)
        if not config.rune_active:
            return
        press(self.config['Interact'], 1, down_time=0.2,
              up_time=0.8)        # Inherited from Configurable

        print('\nSolving rune:')
        used_frame = None
        find_solution = False
        for i in range(10):
            if not config.rune_active:
                return
            frame = capture.frame
            solution = rune.show_magic(frame)
            if solution is None and retry:
                self._solve_rune(retry=False)
                return
            else:
                print(', '.join(solution))
                if len(solution) == 4:
                    print('Solution found, entering result')
                    used_frame = frame
                    find_solution = True
                    for arrow in solution:
                        press(arrow, 1, down_time=0.1)
                    break
            time.sleep(0.1)
        time.sleep(0.3)

        if find_solution:
            threading.Timer(0.001, self.check_rune_solve_result,
                            (used_frame, )).start()
        else:
            self.on_rune_solve_failed(used_frame)

    def check_rune_solve_result(self, used_frame):
        for _ in range(4):
            rune_type = rune.rune_liberate_result(capture.frame)
            if rune_type is not None:
                break
            time.sleep(0.1)
        if rune_type is None:
            self.on_rune_solve_failed(used_frame)
        else:
            notifier.notifyRuneResolved(rune_type)
            # file_path = 'screenshot/rune_solved'
            # utils.save_screenshot(
            #     frame=used_frame, file_path=file_path, compress=False)

            if rune_type == 'Rune of Might':
                ActionSimulator.cancel_rune_buff()

    def on_rune_solve_failed(self, used_frame):
        notifier.notifyRuneResolveFailed()
        file_path = 'screenshot/rune_failed'
        utils.save_screenshot(
            frame=used_frame, file_path=file_path, compress=False)

    @utils.run_if_enabled
    def _mining(self):
        """
        Moves to the position of the rune and solves the arrow-key puzzle.
        :param sct:     The mss instance object with which to take screenshots.
        :return:        None
        """

        if config.hide_start > 0 and time.time() - config.hide_start <= 35:
            return

        move = config.command_book['move']
        move(*config.minal_pos).execute()
        adjust = config.command_book['adjustx']
        adjust(*config.minal_pos).execute()
        time.sleep(0.2)
        
        mineral_template = MINAL_HEART_TEMPLATE
        if config.mineral_type == MineralType.CRYSTAL:
            mineral_template = MINAL_CRYSTAL_TEMPLATE
        elif config.mineral_type == MineralType.HERB_YELLOW:
            mineral_template = HERB_YELLOW_TEMPLATE
        elif config.mineral_type == MineralType.HERB_PURPLE:
            mineral_template = HERB_PURPLE_TEMPLATE
                                    
        matches = utils.multi_match(frame, mineral_template)
        if len(matches) > 0:
            player_template = PLAYER_SLLEE_TEMPLATE if config.command_book.name == 'shadower' else PLAYER_ISSL_TEMPLATE
            player = utils.multi_match(
                frame, player_template, threshold=0.9)
            player_x = player[0][0]
            mineral_x = matches[0][0]
            if config.mineral_type == MineralType.HERB_YELLOW or config.mineral_type == MineralType.HERB_PURPLE:
                mineral_x -= 18
            if mineral_x > player_x:
                if config.player_direction == 'left':
                    press('right')
                if mineral_x - player_x >= 40:
                    press('right', (mineral_x - player_x)//40)
            elif mineral_x < player_x:
                if config.player_direction == 'right':
                    press('left')
                if player_x - mineral_x >= 40:
                    press('left', (player_x - mineral_x)//40)
            else:
                if config.player_direction == 'right':
                    press('right')
                    press('left')
                else:
                    press('left')
                    press('right')
        else:
            if config.player_direction == 'right':
                press('right', 2)
                press('left')
            else:
                press('left', 2)
                press('right')
        time.sleep(0.3)
        # if config.minal_pos[0] > config.player_pos[0]:
        #     if config.player_direction == 'left':
        #         press('right')
        # elif config.minal_pos[0] < config.player_pos[0]:
        #     if config.player_direction == 'right':
        #         press('left')
        # else:
        #     if config.player_direction == 'right':
        #         press('right', 2)
        #         press('left')
        #     else:
        #         press('left', 2)
        #         press('right')

        press(self.config['Interact'], 1, down_time=0.2,
              up_time=0.8)        # Inherited from Configurable

        print('\n mining:')
        frame = capture.frame
        solution = rune.show_magic(frame)
        if solution is not None:
            print(', '.join(solution))
            print('Solution found, entering result')
            for arrow in solution:
                press(arrow, 1, down_time=0.1)
        time.sleep(3.5)
        config.minal_active = False
        config.minal_pos = None
        config.minal_closest_pos = None

    def load_commands(self, file):
        try:
            config.command_book = CommandBook(file)
            config.gui.settings.update_class_bindings()
        except ValueError:
            pass    # TODO: UI warning popup, say check cmd for errors

    def toggle(self, enabled: bool, reason: str = ''):
        config.rune_active = False
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
            f"rune status: {f'{time.time() - notifier.rune_active_time}s' if config.rune_active else 'clear'}\n"
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
                config.gui.settings.notification.notice_level.set(level)
                config.gui.settings.notification.notification_settings.save_config()
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
            match (event_type):
                case BotError.LOST_WINDOW:
                    self.toggle(False, event_type.value)
                case BotError.LOST_MINI_MAP:
                    self.toggle(False, event_type.value)
                case BotError.LOST_PLAYER:
                    self.toggle(False, event_type.value)
                case BotError.BLACK_SCREEN:
                    if arg >= 10:
                        self.toggle(False, event_type.value)
                case BotError.NO_MOVEMENT:
                    pass
                case BotError.RUNE_ERROR:
                    ActionSimulator.go_home()
                case BotError.OTHERS_STAY_OVER_120S:
                    ActionSimulator.go_home()
                case (_):
                    self.toggle(False, event_type.value)
            # end match
        elif isinstance(event_type, BotWarnning):
            match event_type:
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
                case BotInfo.RUNE_ACTIVE:
                    pass
        elif isinstance(event_type, BotDebug):
            pass


bot = Bot()
