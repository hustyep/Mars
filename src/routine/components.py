"""A collection of classes used to execute a Routine."""

import math
import time
from src.common import config, utils, settings
from src.common.vkeys import key_down, key_up, press, releaseAll, press_acc
from src.modules.capture import capture
from src.common.image_template import *

#################################
#       Routine Components      #
#################################


class Component:
    id = 'Routine Component'
    PRIMITIVES = {int, str, bool, float}

    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError(
                'Component superclass __init__ only accepts 1 (optional) argument: LOCALS')
        if len(kwargs) != 0:
            raise TypeError(
                'Component superclass __init__ does not accept any keyword arguments')
        if len(args) == 0:
            self.kwargs = {}
        elif type(args[0]) != dict:
            raise TypeError(
                "Component superclass __init__ only accepts arguments of type 'dict'.")
        else:
            self.kwargs = args[0].copy()
            self.kwargs.pop('__class__')
            self.kwargs.pop('self')

    @utils.run_if_enabled
    def execute(self):
        self.main()

    def main(self):
        self.print_debug_info()

    def update(self, *args, **kwargs):
        """Updates this Component's constructor arguments with new arguments."""

        # Validate arguments before actually updating values
        self.__class__(*args, **kwargs)
        self.__init__(*args, **kwargs)

    def info(self):
        """Returns a dictionary of useful information about this Component."""

        return {
            'name': self.__class__.__name__,
            'vars': self.kwargs.copy()
        }

    def encode(self):
        """Encodes an object using its ID and its __init__ arguments."""

        arr = [self.id]
        for key, value in self.kwargs.items():
            if key != 'id' and type(self.kwargs[key]) in Component.PRIMITIVES:
                arr.append(f'{key}={value}')
        return ', '.join(arr)
    
    def print_debug_info(self):
        if config.notice_level == 5:
            print(self.info())


class Point(Component):
    """Represents a location in a user-defined routine."""

    id = '*'

    def __init__(self, x, y, frequency=1, interval=0, skip='False', adjust='False'):
        super().__init__(locals())
        self.x = int(x)
        self.y = int(y)
        self.location = (self.x, self.y)
        self.frequency = settings.validate_nonnegative_int(frequency)
        self.interval = settings.validate_nonnegative_float(interval)
        if self.interval > 0:
            self.counter = (
                time.time() + 14) if settings.validate_boolean(skip) else 0
        else:
            self.counter = int(settings.validate_boolean(skip))
        self.adjust = settings.validate_boolean(adjust)
        if not hasattr(self, 'commands'):       # Updating Point should not clear commands
            self.commands = []

    def main(self):
        """Executes the set of actions associated with this Point."""
        # self.print_debug_info()

        if self.interval > 0:
            if self.counter == 0 or time.time() - self.counter >= self.interval:
                self._main()
                self.counter = time.time()
        else:
            if self.counter == 0:
                self._main()
            self._increment_counter()
            
            
    def _main(self):
        move = config.command_book['move']
        move(*self.location).execute()
        if self.adjust:
            # TODO: adjust using step('up')?
            adjust = config.command_book['adjust']
            adjust(*self.location).execute()
        for command in self.commands:
            command.execute()
            
    @utils.run_if_enabled
    def _increment_counter(self):
        """Increments this Point's counter, wrapping back to 0 at the upper bound."""

        self.counter = (self.counter + 1) % self.frequency

    def info(self):
        curr = super().info()
        curr['vars'].pop('location', None)
        curr['vars']['commands'] = ', '.join([c.id for c in self.commands])
        return curr

    def __str__(self):
        return f'  * {self.location}'


class Label(Component):
    id = '@'

    def __init__(self, label):
        super().__init__(locals())
        self.label = str(label)
        if self.label in config.routine.labels:
            raise ValueError
        self.links = set()
        self.index = None

    def set_index(self, i):
        self.index = i

    def encode(self):
        return '\n' + super().encode()

    def info(self):
        curr = super().info()
        curr['vars']['index'] = self.index
        return curr

    def __delete__(self, instance):
        del self.links
        config.routine.labels.pop(self.label)

    def __str__(self):
        return f'{self.label}:'


class Jump(Component):
    """Jumps to the given Label."""

    id = '>'

    def __init__(self, label, frequency=1, skip='False'):
        super().__init__(locals())
        self.label = str(label)
        self.frequency = settings.validate_nonnegative_int(frequency)
        self.counter = int(settings.validate_boolean(skip))
        self.link = None

    def main(self):
        if self.link is None:
            print(f"\n[!] Label '{self.label}' does not exist.")
        else:
            if self.counter == 0:
                config.routine.index = self.link.index
            self._increment_counter()

    @utils.run_if_enabled
    def _increment_counter(self):
        self.counter = (self.counter + 1) % self.frequency

    def bind(self):
        """
        Binds this Goto to its corresponding Label. If the Label's index changes, this Goto
        instance will automatically be able to access the updated value.
        :return:    Whether the binding was successful
        """

        if self.label in config.routine.labels:
            self.link = config.routine.labels[self.label]
            self.link.links.add(self)
            return True
        return False

    def __delete__(self, instance):
        if self.link is not None:
            self.link.links.remove(self)

    def __str__(self):
        return f'  > {self.label}'


class Setting(Component):
    """Changes the value of the given setting variable."""

    id = '$'

    def __init__(self, target, value):
        super().__init__(locals())
        self.key = str(target)
        if self.key not in settings.SETTING_VALIDATORS:
            raise ValueError(f"Setting '{target}' does not exist")
        self.value = settings.SETTING_VALIDATORS[self.key](value)

    def main(self):
        setattr(settings, self.key, self.value)

    def __str__(self):
        return f'  $ {self.key} = {self.value}'


SYMBOLS = {
    '*': Point,
    '@': Label,
    '>': Jump,
    '$': Setting
}


#############################
#       Shared Commands     #
#############################
class Command(Component):
    id = 'Command Superclass'
    key: str = None
    cooldown: int = 0
    castedTime: float = 0
    precast: float = 0
    backswing: float = 0.5

    def __init__(self, *args):
        super().__init__(*args)
        self.id = self.__class__.__name__

    def __str__(self):
        variables = self.__dict__
        result = '    ' + self.id
        if len(variables) - 1 > 0:
            result += ':'
        for key, value in variables.items():
            if key != 'id':
                result += f'\n        {key}={value}'
        return result

    def canUse(self, next_t: float = 0) -> bool:
        if self.__class__.cooldown is None:
            return True

        cur_time = time.time()
        if (cur_time + next_t - self.__class__.castedTime) > self.__class__.cooldown + self.__class__.backswing:
            return True

        return False

    def main(self):
        if not self.canUse():
            return False

        if len(self.__class__.key) == 0:
            return False

        super().main()
        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        press_acc(self.__class__.key, up_time=self.__class__.backswing)
        return True


class Move(Command):
    """Moves to a given position using the shortest path based on the current Layout."""

    def __init__(self, x, y, max_steps=15):
        super().__init__(locals())
        self.target = (int(x), int(y))
        self.max_steps = settings.validate_nonnegative_int(max_steps)
        self.prev_direction = ''

    def _new_direction(self, new):
        if new != 'up' and new != 'down':
            # 谨慎按上方向键
            key_down(new)
        if self.prev_direction and self.prev_direction != new:
            key_up(self.prev_direction)
        self.prev_direction = new

    def main(self):
        # self.print_debug_info()
        
        counter = self.max_steps
        path = config.layout.shortest_path(config.player_pos, self.target)
        threshold = settings.move_tolerance / math.sqrt(2)

        if config.notice_level == 5:
            print(f"[move]path: {path}")

        for i, point in enumerate(path):
            self.prev_direction = ''
            local_error = utils.distance(config.player_pos, point)
            global_error = utils.distance(config.player_pos, self.target)

            if config.notice_level == 5 and not (config.player_pos[0] == point[0] and config.player_pos[1] == point[1]):
                print(f'[move] from {config.player_pos} to {point}, target:{self.target}')

            while config.enabled and counter > 0 and \
                    local_error > settings.move_tolerance and \
                    global_error > settings.move_tolerance:
                d_x = point[0] - config.player_pos[0]
                if abs(d_x) > threshold:
                    if d_x < 0:
                        key = 'left'
                    else:
                        key = 'right'
                    self._new_direction(key)
                    step(key, point)
                    if settings.record_layout:
                        config.layout.add(*config.player_pos)
                    if i < len(path) - 1:
                        time.sleep(0.15)
                    counter -= 1
                else:
                    global_d_y = self.target[1] - config.player_pos[1]
                    d_y = point[1] - config.player_pos[1]
                    if abs(global_d_y) > threshold and \
                            abs(d_y) > threshold:
                        if d_y < 0:
                            key = 'up'
                        else:
                            key = 'down'
                        self._new_direction(key)
                        step(key, point)
                        if settings.record_layout:
                            config.layout.add(*config.player_pos)
                        if i < len(path) - 1:
                            time.sleep(0.05)
                        counter -= 1
                if threshold > settings.adjust_tolerance:
                    threshold -= 1
                local_error = utils.distance(config.player_pos, point)
                global_error = utils.distance(config.player_pos, self.target)
            if self.prev_direction:
                key_up(self.prev_direction)


class Adjust(Command):
    def __init__(self, x, y, max_steps=6):
        super().__init__(locals())
        self.target = (int(x), int(y))
        self.max_steps = settings.validate_nonnegative_int(max_steps)

    def main(self):
        # self.print_debug_info()
        
        # print(f'[Adjust] from {config.player_pos} to {self.target}')

        counter = self.max_steps
        d_x = self.target[0] - config.player_pos[0]
        d_y = self.target[1] - config.player_pos[1]
        threshold = settings.adjust_tolerance / math.sqrt(2)
        
        while config.enabled and counter > 0 and (abs(d_x) > threshold or abs(d_y) > threshold):
            if abs(d_x) > settings.move_tolerance:
                Move(*self.target)
                return
            elif abs(d_x) > threshold:
                walk_counter = 0
                if d_x < 0:
                    key_down('left')
                    while config.enabled and d_x < -1 * threshold and walk_counter < 60:
                        time.sleep(0.01)
                        walk_counter += 1
                        d_x = self.target[0] - config.player_pos[0]
                    key_up('left')
                else:
                    key_down('right')
                    while config.enabled and d_x > threshold and walk_counter < 60:
                        time.sleep(0.01)
                        walk_counter += 1
                        d_x = self.target[0] - config.player_pos[0]
                    key_up('right')
                counter -= 1
            elif abs(d_y) > threshold:
                if d_y < 0:
                    MoveUp(dy=abs(d_y)).execute()
                else:
                    MoveDown(dy=abs(d_y)).execute()
                counter -= 1
            d_x = self.target[0] - config.player_pos[0]
            d_y = self.target[1] - config.player_pos[1]


class AdjustX(Command):
    def __init__(self, x, y, max_steps=10):
        super().__init__(locals())
        self.target = (int(x), int(y))
        self.max_steps = settings.validate_nonnegative_int(max_steps)

    def main(self):
        print(f'[AdjustX] from {config.player_pos} to {self.target}')
        
        counter = self.max_steps
        d_x = self.target[0] - config.player_pos[0]
        d_y = self.target[1] - config.player_pos[1]
        threshold_x = 1
        threshold_y = 5
        while config.enabled and counter > 0 and (abs(d_x) > threshold_x or abs(d_y) > threshold_y):
            if abs(d_x) > settings.move_tolerance:
                Move(*self.target)
                return
            elif abs(d_x) > threshold_x:
                walk_counter = 0
                if d_x < 0:
                    key_down('left')
                    while config.enabled and d_x < -1 * threshold_x and walk_counter < 60:
                        time.sleep(0.01)
                        walk_counter += 1
                        d_x = self.target[0] - config.player_pos[0]
                    key_up('left')
                else:
                    key_down('right')
                    while config.enabled and d_x > threshold_x and walk_counter < 60:
                        time.sleep(0.01)
                        walk_counter += 1
                        d_x = self.target[0] - config.player_pos[0]
                    key_up('right')
                counter -= 1
            elif abs(d_y) > threshold_y:
                if d_y < 0:
                    MoveUp(dy=abs(d_y)).execute()
                else:
                    MoveDown(dy=abs(d_y)).execute()
                counter -= 1
            d_x = self.target[0] - config.player_pos[0]
            d_y = self.target[1] - config.player_pos[1]


class MoveUp(Command):
    """Undefined 'moveup' command for the default command book."""

    def __init__(self, dy: int = 20):
        super().__init__(locals())
        self.dy = abs(dy)

    def main(self):
        print(
            "\n[!] 'MoveUp' command not implemented in current command book, aborting process.")
        config.enabled = False


class MoveDown(Command):
    """Undefined 'movedown' command for the default command book."""

    def __init__(self, dy: int = 20):
        super().__init__(locals())
        self.dy = abs(dy)

    def main(self):
        print(
            "\n[!] 'MoveDown' command not implemented in current command book, aborting process.")
        config.enabled = False


def step(direction, target):
    """
    The default 'step' function. If not overridden, immediately stops the bot.
    :param direction:   The direction in which to move.
    :param target:      The target location to step towards.
    :return:            None
    """

    print("\n[!] Function 'step' not implemented in current command book, aborting process.")
    config.enabled = False


class Wait(Command):
    """Waits for a set amount of time."""

    def __init__(self, duration):
        super().__init__(locals())
        self.duration = float(duration)

    def main(self):
        self.print_debug_info()

        releaseAll()
        time.sleep(self.duration)


class Walk(Command):
    """Walks in the given direction for a set amount of time."""

    def __init__(self, direction, duration):
        super().__init__(locals())
        self.direction = settings.validate_horizontal_arrows(direction)
        self.duration = float(duration)

    def main(self):
        key_down(self.direction)
        time.sleep(self.duration)
        key_up(self.direction)
        time.sleep(0.05)


class Fall(Command):
    """
    Performs a down-jump and then free-falls until the player exceeds a given distance
    from their starting position.
    """

    def __init__(self, distance=settings.move_tolerance / 2):
        super().__init__(locals())
        self.distance = float(distance)
        print("fall")

    def main(self):
        start = config.player_pos
        key_down('down')
        time.sleep(0.05)
        if config.stage_fright and utils.bernoulli(0.5):
            time.sleep(utils.rand_float(0.2, 0.4))
        counter = 6
        while config.enabled and \
                counter > 0 and \
                utils.distance(start, config.player_pos) < self.distance:
            press('s', 1, down_time=0.1)
            counter -= 1
        key_up('down')
        time.sleep(0.05)


class Buff(Command):
    """Undefined 'buff' command for the default command book."""

    def main(self):
        self.print_debug_info()

        print(
            "\n[!] 'Buff' command not implemented in current command book, aborting process.")
        config.enabled = False


class Potion(Command):
    """Undefined 'potion' command for the default command book."""

    def main(self):
        self.print_debug_info()

        print(
            "\n[!] 'potion' command not implemented in current command book, aborting process.")
        config.enabled = False


class Detect_Mobs(Command):
    def __init__(self, top=0, left=0, right=0, bottom=0):
        super().__init__(locals())
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right
        # print("Detect_Mobs")

    @utils.run_if_enabled
    def execute(self):
        return self.main()

    def main(self):
        frame = capture.frame
        minimap = capture.minimap

        if frame is None or minimap is None:
            return False

        if not config.mob_detect:
            return True

        if len(config.routine.mob_template) == 0:
            return True
                    
        player_template = PLAYER_SLLEE_TEMPLATE if config.command_book.name == 'shadower' else PLAYER_ISSL_TEMPLATE
        player_match = utils.multi_match(
            capture.frame, player_template, threshold=0.9)
        if len(player_match) == 0:
            return True
        
        player_pos = (player_match[0][0] - 5, player_match[0][1] - 55)
        crop = frame[player_pos[1]-self.top:player_pos[1]+self.bottom, player_pos[0]-self.left:player_pos[0]+self.right]
        
        for mob_template in config.routine.mob_template:
            mobs_tmp = utils.multi_match(crop, mob_template, threshold=0.9)
            if len(mobs_tmp) > 0:
                return True

        return False
    
#############################
#      Shared Functions     #
#############################

def sleep_while_move_y(interval=0.02, n=6):
    player_y = config.player_pos[1]
    count = 0
    while True:
        time.sleep(interval)
        if player_y == config.player_pos[1]:
            count += 1
        else:
            count = 0
            player_y = config.player_pos[1]
        if count == n:
            break

def direction_changed():
    if config.player_direction == 'left':
        return abs(config.routine.guard_point_r[0] - config.player_pos[0]) <= 1.3 * settings.move_tolerance
    else:
        return abs(config.routine.guard_point_l[0] - config.player_pos[0]) <= 1.3 * settings.move_tolerance