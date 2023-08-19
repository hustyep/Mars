"""A collection of all commands that Night Lord can use to interact with the game. 	"""

from src.common import config, settings, utils
import time
import math
from src.routine.components import Command
from src.common.vkeys import press, key_down, key_up, releaseAll, press_acc


# List of key mappings
class Key:
    # Movement
    JUMP = 's'
    FLASH_JUMP = ';'
    SHADOW_LEAP = 'a'
    SHADOW_SURGE = 'g'
    ROPE_LIFT = 'b'

    # Buffs
    GODDESS_BLESSING = '1'
    LAST_RESORT = '2'
    EPIC_ADVENTURE = '4'
    MEMORIES = '5'
    MAPLE_WARRIOR = '6'
    SHADOW_WALKER = 'shift'
    THROW_BLASTING = 'v'
    FOR_THE_GUILD = '7'
    HARD_HITTER = '8'
    
    # Potion
    EXP_POTION = '0'
    WEALTH_POTION = "-"
    GOLD_POTION = "="
    GUILD_POTION = "9"
    
    # SHADOW_PARTNER = '3'
    # SPEED_INFUSION = '8'
    # HOLY_SYMBOL = '4'
    # SHARP_EYE = '5'
    # COMBAT_ORDERS = '6'
    # ADVANCED_BLESSING = '7'

    # Skills
    SHOW_DOWN = 'd'
    SUDDEN_RAID = 'r'
    OMEN = 'x'
    ARACHNID = 'q'
    SHURIKEN = 'c'
    DARK_FLARE = 'w'
    ERDA_SHOWER = '`' 


#########################
#       Movement        #
#########################

@utils.run_if_enabled
def step(direction, target):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    Should not press any arrow keys, as those are handled by Mars.
    """

    if config.stage_fright and direction != 'up' and utils.bernoulli(0.75):
        time.sleep(utils.rand_float(0.1, 0.3))
        
    d_x = abs(target[0] - config.player_pos[0])
    d_y = abs(target[1] - config.player_pos[1])
    # if d_y > settings.move_tolerance * 1.5:
    if direction == 'down':
        # print(f"step_down: {d_y}")
        if d_y > settings.move_tolerance:
            press_acc(Key.JUMP, 2, down_time=0.1,up_time=0.1)
            time.sleep(d_y)
        return
    elif direction == 'up':
        # print(f"step_up: {d_y}")
        MoveUp(dy=d_y)
        return
        
    if d_x >=0.11:
        press(Key.JUMP, 1, down_time=0.04, up_time=0.05)
        press(Key.FLASH_JUMP, 1, down_time=0.04, up_time=0.05)
        ShowDown().execute()
    else:
        time.sleep(0.05)
    
    # if direction == "left" or direction == "right":


class Adjust(Command):
    """Fine-tunes player position using small movements."""

    def __init__(self, x, y, max_steps=5):
        super().__init__(locals())
        self.target = (float(x), float(y))
        self.max_steps = settings.validate_nonnegative_int(max_steps)
        # print(f'adjust: {self.target}')

    def main(self):
        counter = self.max_steps
        toggle = True
        error = utils.distance(config.player_pos, self.target)
        while config.enabled and counter > 0 and error > settings.adjust_tolerance:
            if toggle:
                d_x = self.target[0] - config.player_pos[0]
                threshold = settings.adjust_tolerance / math.sqrt(2)
                if abs(d_x) > threshold:
                    walk_counter = 0
                    if d_x < 0:
                        key_down('left')
                        while config.enabled and d_x < -1 * threshold and walk_counter < 60:
                            time.sleep(0.05)
                            walk_counter += 1
                            d_x = self.target[0] - config.player_pos[0]
                        key_up('left')
                    else:
                        key_down('right')
                        while config.enabled and d_x > threshold and walk_counter < 60:
                            time.sleep(0.05)
                            walk_counter += 1
                            d_x = self.target[0] - config.player_pos[0]
                            # print(f'dx: {d_x}; threshold: {threshold}')
                        key_up('right')
                    counter -= 1
            else:
                d_y = self.target[1] - config.player_pos[1]
                if abs(d_y) > settings.adjust_tolerance / math.sqrt(2):
                    if d_y < 0:
                        print(f"adjust up {d_y}")
                        releaseAll()
                        MoveUp(d_y).execute()
                    else:
                        print(f"adjust down {d_y}")
                        key_down('down')
                        time.sleep(0.05)
                        press(Key.JUMP, 2, down_time=0.2, up_time=0.3)
                        key_up('down')
                        time.sleep(0.05)
                    counter -= 1
            error = utils.distance(config.player_pos, self.target)
            toggle = not toggle
            
class Move(Command):
    """Moves to a given position using the shortest path based on the current Layout."""

    def __init__(self, x, y, max_steps=15):
        super().__init__(locals())
        self.target = (float(x), float(y))
        self.max_steps = settings.validate_nonnegative_int(max_steps)
        self.prev_direction = ''

    def _new_direction(self, new):
        if new != 'up':
            # 谨慎按上方向键
            key_down(new)
        if self.prev_direction and self.prev_direction != new:
            key_up(self.prev_direction)
        self.prev_direction = new

    def main(self):
        counter = self.max_steps
        path = config.layout.shortest_path(config.player_pos, self.target)
        for i, point in enumerate(path):
            toggle = True
            self.prev_direction = ''
            local_error = utils.distance(config.player_pos, point)
            global_error = utils.distance(config.player_pos, self.target)
            
            if global_error <= settings.move_tolerance:
                break
            
            while config.enabled and counter > 0 and \
                    local_error > settings.move_tolerance and \
                    global_error > settings.move_tolerance:
                if toggle:
                    d_x = point[0] - config.player_pos[0]
                    if abs(d_x) > settings.move_tolerance / math.sqrt(2):
                        if d_x < 0:
                            key = 'left'
                        else:
                            key = 'right'
                        self._new_direction(key)
                        step(key, point)
                        if settings.record_layout:
                            config.layout.add(*config.player_pos)
                        counter -= 1
                        if i < len(path) - 1:
                            time.sleep(0.15)
                else:
                    global_d_y = self.target[1] - config.player_pos[1]
                    d_y = point[1] - config.player_pos[1]
                    if abs(global_d_y) > settings.move_tolerance / math.sqrt(2) and \
                        abs(d_y) > settings.move_tolerance / math.sqrt(2):
                        if d_y < 0:
                            key = 'up'
                        else:
                            key = 'down'
                        # print(f"move down: {local_error} | {global_error}" )
                        self._new_direction(key)
                        step(key, point)
                        if settings.record_layout:
                            config.layout.add(*config.player_pos)
                        counter -= 1
                        if i < len(path) - 1:
                            time.sleep(0.05)
                local_error = utils.distance(config.player_pos, point)
                global_error = utils.distance(config.player_pos, self.target)
                toggle = not toggle
            if self.prev_direction:
                key_up(self.prev_direction)

# y轴移动
class MoveUp(Command):
    def __init__(self, dy: float = 0.2):
        super().__init__(locals())
        self.dy = abs(dy)
        
    def main(self):
        if self.dy <= 0.125:
            ShadowLeap(True if self.dy >= 0.11 else False).execute()
        else:
            RopeLift(self.dy).execute()
        

# 二段跳
class FlashJump(Command):
    """Performs a flash jump in the given direction."""

    def __init__(self, direction):
        super().__init__(locals())
        self.direction = settings.validate_arrows(direction)

    def main(self):
        key_down(self.direction)
        time.sleep(0.1)
        press(Key.JUMP, 1, down_time=0.04, up_time=0.05)
        press(Key.FLASH_JUMP, 1, down_time=0.04, up_time=0.05)
        key_up(self.direction)
        time.sleep(0.5)


# 上跳
class ShadowLeap(Command):
    key = Key.SHADOW_LEAP
    precast = 0.5
    backswing = 0.75

    def __init__(self, jump: bool = False):
        super().__init__(locals())
        self.jump = jump

    def main(self):
        time.sleep(self.__class__.precast)
        if self.jump:
            press_acc(Key.JUMP, down_time=0.05, up_time=0.03)

        press_acc(self.__class__.key, up_time=self.__class__.backswing)


# 水平位移
class ShadowSurge(Command):
    key = Key.SHADOW_SURGE
    cooldown = 10
    backswing = 1

# 绳索
class RopeLift(Command):
    key = Key.ROPE_LIFT
    cooldown = 3

    def __init__(self, dy: float = 0.2):
        super().__init__(locals())
        self.dy = dy

    def main(self):
        if self.dy >= 0.3:
            press(Key.JUMP, up_time=0.12)
        press_acc(self.__class__.key, up_time=self.dy * 9.5)
        if self.dy >= 0.3:
            time.sleep(self.dy * 3)
        # if self.cancel is not None:
        #     time.sleep(self.cancel)
        #     press(self.__class__.key)


#######################
#       Summon        #
#######################


class DarkFlare(Command):
    """
    Uses 'DarkFlare' in a given direction, or towards the center of the map if
    no direction is specified.
    """
    cooldown = 120
    backswing = 0.75

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = settings.validate_horizontal_arrows(direction)

    def main(self):
        if self.direction:
            press(self.direction, 1, down_time=0.05, up_time=0.05)
        else:
            if config.player_pos[0] > 0.5:
                press('left', 1, down_time=0.1, up_time=0.05)
            else:
                press('right', 1, down_time=0.1, up_time=0.05)
        press(Key.DARK_FLARE, 1, up_time=self.__class__.backswing)


class ErdaShower(Command):
    """
    Use ErdaShower in a given direction, Placing ErdaFountain if specified. Adds the player's position
    to the current Layout if necessary.
    """
    cooldown = 120
    backswing = 0.6

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = settings.validate_horizontal_arrows(direction)

    def main(self):
        if self.direction:
            press(self.direction, 1, down_time=0.05, up_time=0.05)
        key_down('down')
        press(Key.ERDA_SHOWER, 1, up_time=self.__class__.backswing)
        key_up('down')


#######################
#       Skills        #
#######################


class ShowDown(Command):
    key = Key.SHOW_DOWN
    backswing = 0.54

    def main(self):
        time.sleep(self.__class__.precast)
        self.__class__.castedTime = time.time()
        press_acc(self.__class__.key, up_time=self.__class__.backswing)


class SuddenRaid(Command):
    key = Key.SUDDEN_RAID
    cooldown = 30
    backswing = 0.8


class Omen(Command):
    key = Key.OMEN
    cooldown = 60
    backswing = 0.8


class Arachnid(Command):
    key = Key.ARACHNID
    cooldown = 250
    backswing = 0.9


class SHURIKEN(Command):
    key = Key.SHURIKEN
    cooldown = 20
    backswing = 0.8

    def __init__(self, stop: float = None):
        super().__init__(locals())
        self.stop = stop

    def main(self):
        press(self.__class__.key, up_time=0)
        if self.stop is not None:
            time.sleep(self.stop)
            press(self.__class__.key, up_time=0)
            time.sleep(max(self.__class__.backswing - self.stop, 0))
        else:
            time.sleep(self.__class__.backswing)


###################
#      Buffs      #
###################

class Buff(Command):
    """Uses each of Shadowers's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.buffs = [GODDESS_BLESSING(),
                      LAST_RESORT(),
                      EPIC_ADVENTURE(),
                      MEMORIES(),
                      MAPLE_WARRIOR(),
                      SHADOW_WALKER(),
                      THROW_BLASTING(),
                      FOR_THE_GUILD(),
                      HARD_HITTER()]

    def main(self):
        for buff in self.buffs:
            if buff.canUse():
                buff.main()
                break


class GODDESS_BLESSING(Command):
    key = Key.GODDESS_BLESSING
    cooldown = 180
    backswing = 0.75


class LAST_RESORT(Command):
    key = Key.LAST_RESORT
    cooldown = 75
    backswing = 0.75


class EPIC_ADVENTURE(Command):
    key = Key.EPIC_ADVENTURE
    cooldown = 120
    backswing = 0.75


class MEMORIES(Command):
    key = Key.MEMORIES
    cooldown = 150
    backswing = 1


class MAPLE_WARRIOR(Command):
    key = Key.MAPLE_WARRIOR
    cooldown = 900
    backswing = 0.75


class SHADOW_WALKER(Command):
    key = Key.SHADOW_WALKER
    cooldown = 190
    backswing = 0.8


class THROW_BLASTING(Command):
    key = Key.THROW_BLASTING
    cooldown = 180
    backswing = 0.8
    
class FOR_THE_GUILD(Command):
    key = Key.FOR_THE_GUILD
    cooldown = 3610
    backswing = 0.1
    
    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Guild Buff')
        if not enabled:
            return False
        
        if time.time() - HARD_HITTER.castedTime <= 1800 and HARD_HITTER.castedTime > 0:
            return False
        
        return super().canUse(next_t)  

class HARD_HITTER(Command):
    key = Key.HARD_HITTER
    cooldown = 3610
    backswing = 0.1
    
    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Guild Buff')
        if not enabled:
            return False
        
        if time.time() - FOR_THE_GUILD.castedTime <= 1800:
            return False
        
        return super().canUse(next_t)  
    
class EXP_POTION(Command):
    key = Key.EXP_POTION
    cooldown = 7250
    backswing = 0
    
    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Exp Potion')
        if not enabled:
            return False
        
        return super().canUse(next_t)  
        
class WEALTH_POTION(Command):
    key = Key.WEALTH_POTION
    cooldown = 7250
    backswing = 0
    
    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Wealthy Potion')
        if not enabled:
            return False
        
        return super().canUse(next_t)  
    
class GOLD_POTION(Command):
    key = Key.GOLD_POTION
    cooldown = 1800
    backswing = 0
    
    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Gold Potion')
        if not enabled:
            return False
        
        return super().canUse(next_t)  
    
class GUILD_POTION(Command):
    key = Key.GUILD_POTION
    cooldown = 1800
    backswing = 0
    
    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Guild Potion')
        if not enabled:
            return False
        
        return super().canUse(next_t)          