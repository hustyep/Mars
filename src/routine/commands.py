from src.routine.components import *
from src.common.vkeys import key_down, key_up, press, releaseAll, press_acc
from src.modules.capture import capture
from src.common.image_template import *
from src.detection import rune
from src.modules.notifier import notifier
from src.common.action_simulator import ActionSimulator
from src.modules.detector import MineralType
from src.common.bot_notification import BotWarnning
import threading
import math

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
                    while config.enabled and d_x < -1 * threshold and walk_counter < 120:
                        time.sleep(0.005)
                        walk_counter += 1
                        d_x = self.target[0] - config.player_pos[0]
                    key_up('left')
                else:
                    key_down('right')
                    while config.enabled and d_x > threshold and walk_counter < 120:
                        time.sleep(0.005)
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
                    while config.enabled and d_x < -1 * threshold_x and walk_counter < 120:
                        time.sleep(0.005)
                        walk_counter += 1
                        d_x = self.target[0] - config.player_pos[0]
                    key_up('left')
                else:
                    key_down('right')
                    while config.enabled and d_x > threshold_x and walk_counter < 120:
                        time.sleep(0.005)
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

class SolveRune(Command):
    """
    Moves to the position of the rune and solves the arrow-key puzzle.
    :param sct:     The mss instance object with which to take screenshots.
    :return:        None
    """
    cooldown = 8
    
    def __init__(self, retry=False):
        super().__init__(locals())
        self.retry = retry
    
    def canUse(self, next_t: float = 0) -> bool:
        return super().canUse(next_t) and config.rune_pos is not None

    def main(self):
        if not self.canUse():
            return False
        
        Move(*config.rune_pos).execute()
        Adjust(*config.rune_pos).execute()
        time.sleep(0.5)
        press('space', 1, down_time=0.2, up_time=0.8)        # Inherited from Configurable
        interact_result = False
        for _ in range(3):
            interact_result = rune.rune_interact_result(capture.frame)
            if interact_result:
                break
            else:
                time.sleep(0.2)

        if interact_result:
            self.__class__.castedTime = time.time()
        else:
            if not self.retry:
                SolveRune(retry=True).execute()
            else:
                notifier._notify(BotWarnning.RUNE_INTERACT_FAILED)
            return

        print('\nSolving rune:')
        used_frame = None
        find_solution = False
        for i in range(4):
            if config.rune_pos is None:
                return
            frame = capture.frame
            solution = rune.show_magic(frame)
            if solution is None:
                return
            if len(solution) == 4:
                print('Solution found, entering result')
                print(', '.join(solution))
                used_frame = frame
                find_solution = True
                for arrow in solution:
                    press(arrow, 1, down_time=0.1)
                break
            time.sleep(0.1)
        time.sleep(0.2)

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

class Mining(Command):
    """
    Moves to the position of the rune and solves the arrow-key puzzle.
    :param sct:     The mss instance object with which to take screenshots.
    :return:        None
    """
    def main(self):
        if config.hide_start > 0 and time.time() - config.hide_start <= 35:
            return

        Move(*config.minal_pos).execute()
        Adjust(*config.minal_pos).execute()
        time.sleep(0.2)

        mineral_template = MINAL_HEART_TEMPLATE
        if config.mineral_type == MineralType.CRYSTAL:
            mineral_template = MINAL_CRYSTAL_TEMPLATE
        elif config.mineral_type == MineralType.HERB_YELLOW:
            mineral_template = HERB_YELLOW_TEMPLATE
        elif config.mineral_type == MineralType.HERB_PURPLE:
            mineral_template = HERB_PURPLE_TEMPLATE

        frame = capture.frame
        matches = utils.multi_match(frame, mineral_template)
        player_template = config.routine.role_template
        player = utils.multi_match(
            frame, player_template, threshold=0.9)
        if len(matches) > 0 and len(player) > 0:
            player_x = player[0][0]
            mineral_x = matches[0][0]
            if config.mineral_type == MineralType.HERB_YELLOW or config.mineral_type == MineralType.HERB_PURPLE:
                mineral_x -= 18
            if mineral_x > player_x:
                if config.player_direction == 'left':
                    press('right')
                if mineral_x - player_x >= 50:
                    press('right', (mineral_x - player_x)//50)
            elif mineral_x < player_x:
                if config.player_direction == 'right':
                    press('left')
                if player_x - mineral_x >= 50:
                    press('left', (player_x - mineral_x)//50)
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

        press('space', 1, down_time=0.2, up_time=0.8)        # Inherited from Configurable

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

from enum import Enum, auto

class MobType(Enum):
    NORMAL = 'normal mob'
    ELITE = 'elite mob'
    BOSS = 'boss mob'

class Detect_Mobs(Command):
    def __init__(self, top=0, left=0, right=0, bottom=0, type:MobType=MobType.NORMAL, debug=False):
        super().__init__(locals())
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right
        self.type = type
        self.debug = debug
        # print("Detect_Mobs")

    @utils.run_if_enabled
    def execute(self):
        result = self.main()
        if result is not None and len(result) > 0:
            print(f"Detected {self.type.value}: {len(result)}")
        return result

    def main(self):
        frame = capture.frame
        minimap = capture.minimap

        if frame is None or minimap is None:
            return []

        match (self.type):
            case (MobType.BOSS):
                mob_templates = config.routine.boss_template
            case (MobType.ELITE):
                mob_templates = config.routine.elite_template
            case (_):
                mob_templates = config.routine.mob_template
                
        if len(mob_templates) == 0:
            raise ValueError(f"Miss {self.type.value} template")
        
        if config.routine.role_template is None:
            raise ValueError('Miss Role template')
                  
        player_match = utils.multi_match(
            capture.frame, config.routine.role_template, threshold=0.9)
        if len(player_match) == 0:
            print("lost player")
            return [(0,0)] if self.type == MobType.NORMAL else []
        
        player_pos = (player_match[0][0] - 5, player_match[0][1] - 55)
        y_start = max(0, player_pos[1]-self.top)
        x_start = max(0, player_pos[0]-self.left)
        crop = frame[y_start:player_pos[1]+self.bottom, x_start:player_pos[0]+self.right]
        
        mobs = []
        for mob_template in mob_templates:
            mobs_tmp = utils.multi_match(crop, mob_template, threshold=0.95, debug=self.debug)
            if len(mobs_tmp) > 0:
                for mob in mobs_tmp:
                    mobs.append(mob)

        return mobs
    
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
        
def sleep_before_y(target_y, tolorance=0):
    count = 0
    while abs(config.player_pos[1] - target_y) > tolorance:
        time.sleep(0.02)
        count += 1
        if count == 20:
            break

def direction_changed():
    if config.player_direction == 'left':
        return abs(config.routine.guard_point_r[0] - config.player_pos[0]) <= 1.3 * settings.move_tolerance
    else:
        return abs(config.routine.guard_point_l[0] - config.player_pos[0]) <= 1.3 * settings.move_tolerance