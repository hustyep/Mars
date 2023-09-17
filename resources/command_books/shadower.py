"""A collection of all commands that Shadower can use to interact with the game. 	"""

from src.common import config, settings, utils
import time
import math
from src.routine.components import Command
from src.common.vkeys import press, key_down, key_up


# List of key mappings
class Key:
    # Movement
    JUMP = 's'
    FLASH_JUMP = ';'
    SHADOW_ASSAULT = 'g'
    ROPE_LIFT = 'b'

    # Buffs
    GODDESS_BLESSING = '1'
    EPIC_ADVENTURE = ''
    LAST_RESORT = '2'
    MAPLE_WARRIOR = '3'
    SHADOW_WALKER = 'shift'
    THROW_BLASTING = 'v'
    FOR_THE_GUILD = '7'
    HARD_HITTER = '8'

    # Potion
    EXP_POTION = '0'
    WEALTH_POTION = "-"
    GOLD_POTION = "="
    GUILD_POTION = "9"
    CANDIED_APPLE = '6'
    LEGION_WEALTHY = ''
    EXP_COUPON = ''

    # Skills
    CRUEL_STAB = 'f'
    MESO_EXPLOSION = 'd'
    SUDDEN_RAID = 'r'
    DARK_FLARE = 'w'
    SHADOW_VEIL = 'x'
    ARACHNID = 'h'
    ERDA_SHOWER = '`'
    TRICKBLADE = 'a'
    SLASH_SHADOW_FORMATION = 'c'
    SONIC_BLOW = 'z'


#########################
#       Commands        #
#########################
def step(direction, target):
    """
    Performs one movement step in the given DIRECTION towards TARGET.
    Should not press any arrow keys, as those are handled by Mars.
    """

    if config.stage_fright and direction != 'up' and utils.bernoulli(0.75):
        time.sleep(utils.rand_float(0.1, 0.3))
    d_x = abs(target[0] - config.player_pos[0])
    d_y = target[1] - config.player_pos[1]
    if direction == "up":
        MoveUp(dy=abs(d_y)).execute()
    elif direction == "down":
        MoveDown(dy=abs(d_y)).execute()
    elif d_x >= 26:
        # FlashJump(dx=d_x)
        press(Key.JUMP, 1, down_time=0.03, up_time=0.03)
        press(Key.FLASH_JUMP, 1, down_time=0.04, up_time=0.04)
        CruelStabRandomDirection().execute()
    else:
        time.sleep(0.01)


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
        counter = self.max_steps
        path = config.layout.shortest_path(config.player_pos, self.target)
        threshold = settings.move_tolerance / math.sqrt(2)

        for i, point in enumerate(path):
            toggle = True
            self.prev_direction = ''
            local_error = utils.distance(config.player_pos, point)
            global_error = utils.distance(config.player_pos, self.target)

            while config.enabled and counter > 0 and \
                    local_error > settings.move_tolerance and \
                    global_error > settings.move_tolerance:
                if toggle:
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
                        counter -= 1
                        if i < len(path) - 1:
                            time.sleep(0.15)
                else:
                    global_d_y = self.target[1] - config.player_pos[1]
                    d_y = point[1] - config.player_pos[1]
                    if abs(global_d_y) > threshold and \
                            abs(d_y) > threshold:
                        if d_y < 0:
                            key = 'up'
                        else:
                            key = 'down'
                        print(f"move down: {local_error} | {global_error}")
                        self._new_direction(key)
                        step(key, point)
                        if settings.record_layout:
                            config.layout.add(*config.player_pos)
                        counter -= 1
                        if i < len(path) - 1:
                            time.sleep(0.05)
                        if threshold > settings.adjust_tolerance:
                            threshold -= 2
                local_error = utils.distance(config.player_pos, point)
                global_error = utils.distance(config.player_pos, self.target)
                toggle = abs(point[0] - config.player_pos[0]) > threshold
            if self.prev_direction:
                key_up(self.prev_direction)


class AdjustX(Command):
    def __init__(self, x, y, max_steps=10):
        super().__init__(locals())
        self.target = (int(x), int(y))
        self.max_steps = settings.validate_nonnegative_int(max_steps)

    def main(self):
        counter = self.max_steps
        d_x = self.target[0] - config.player_pos[0]
        d_y = self.target[1] - config.player_pos[1]
        threshold_x = 2
        threshold_y = 5
        while config.enabled and counter > 0 and (abs(d_x) > threshold_x or abs(d_y) > threshold_y):
            if abs(d_x) > threshold_x:
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
            if abs(d_y) > threshold_y:
                if d_y < 0:
                    MoveUp(dy=abs(d_y)).execute()
                else:
                    MoveDown(dy=abs(d_y)).execute()
                counter -= 1
            d_x = self.target[0] - config.player_pos[0]
            d_y = self.target[1] - config.player_pos[1]

class Adjust(Command):
    def __init__(self, x, y, max_steps=6):
        super().__init__(locals())
        self.target = (int(x), int(y))
        self.max_steps = settings.validate_nonnegative_int(max_steps)

    def main(self):
        counter = self.max_steps
        d_x = self.target[0] - config.player_pos[0]
        d_y = self.target[1] - config.player_pos[1]
        threshold = 2
        while config.enabled and counter > 0 and (abs(d_x) > threshold or abs(d_y) > threshold):
            if abs(d_x) > threshold:
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
            if abs(d_y) > threshold:
                if d_y < 0:
                    MoveUp(dy=abs(d_y)).execute()
                else:
                    MoveDown(dy=abs(d_y)).execute()
                counter -= 1
            d_x = self.target[0] - config.player_pos[0]
            d_y = self.target[1] - config.player_pos[1]

            
# class Adjust(Command):
#     """Fine-tunes player position using small movements."""

#     def __init__(self, x, y, max_steps=5):
#         super().__init__(locals())
#         self.target = (int(x), int(y))
#         self.max_steps = settings.validate_nonnegative_int(max_steps)

#     def main(self):
#         counter = self.max_steps
#         toggle = True
#         error = utils.distance(config.player_pos, self.target)
#         threshold = settings.adjust_tolerance / math.sqrt(2)
#         while config.enabled and counter > 0 and error > settings.adjust_tolerance:
#             if toggle:
#                 d_x = self.target[0] - config.player_pos[0]
#                 if abs(d_x) > threshold:
#                     walk_counter = 0
#                     if d_x < 0:
#                         key_down('left')
#                         while config.enabled and d_x < -1 * threshold and walk_counter < 60:
#                             time.sleep(0.05)
#                             walk_counter += 1
#                             d_x = self.target[0] - config.player_pos[0]
#                         key_up('left')
#                     else:
#                         key_down('right')
#                         while config.enabled and d_x > threshold and walk_counter < 60:
#                             time.sleep(0.05)
#                             walk_counter += 1
#                             d_x = self.target[0] - config.player_pos[0]
#                         key_up('right')
#                     counter -= 1
#             else:
#                 d_y = self.target[1] - config.player_pos[1]
#                 if abs(d_y) > threshold:
#                     if d_y < 0:
#                         MoveUp(dy=abs(d_y)).execute()
#                     else:
#                         MoveDown(dy=abs(d_y)).execute()
#                     counter -= 1
#             error = utils.distance(config.player_pos, self.target)
#             toggle = not toggle

# y轴移动


class MoveUp(Command):
    def __init__(self, dy: int = 20):
        super().__init__(locals())
        self.dy = abs(dy)

    def main(self):
        if self.dy <= 6:
            press(Key.JUMP, up_time=1)
        elif self.dy <= 24:
            JumpUp(dy=self.dy).execute()
        elif self.dy <= 40 and ShadowAssault().canUse():
            ShadowAssault('up', jump='True', distance=self.dy).execute()
        else:
            RopeLift(dy=self.dy).execute()

class MoveDown(Command):
    def __init__(self, dy: int = 20):
        super().__init__(locals())
        self.dy = abs(dy)
            
    def main(self):
        key_down('down')
        press(Key.JUMP, 1, down_time=0.2, up_time=0.08)
        key_up('down')
        time.sleep(0.6)


class JumpUp(Command):
    def __init__(self, dy: int = 20):
        super().__init__(locals())
        self.dy = abs(dy)

    def main(self):
        time.sleep(0.5)
        press(Key.JUMP)
        key_down('up')
        time.sleep(0.06 if self.dy >= 20 else 0.1)
        press(Key.FLASH_JUMP, 1)
        key_up('up')
        time.sleep(1.5)


class FlashJump(Command):
    """Performs a flash jump in the given direction."""

    def __init__(self, time = 1, dx = None):
        super().__init__(locals())
        
        if dx is not None:
            self.time = 1 if dx <= 40 else 2
        else:
            self.time = time

    def main(self):
        time.sleep(0.5)
        press(Key.JUMP, 1)
        # key_down(self.direction)
        time.sleep(0.08)
        press(Key.FLASH_JUMP, self.time)
        # key_up(self.direction)
        time.sleep(1.2)


class ShadowAssault(Command):
    """
    ShadowAssault in a given direction, jumping if specified. Adds the player's position
    to the current Layout if necessary.
    """

    backswing = 0.85
    usable_times = 4
    cooldown = 60

    def __init__(self, direction='up', jump='False', distance=80):
        super().__init__(locals())
        self.direction = settings.validate_arrows(direction)
        self.jump = settings.validate_boolean(jump)
        self.distance = distance
        
    def canUse(self, next_t: float = 0) -> bool:

        if self.__class__.usable_times > 0:
            return True

        cur_time = time.time()
        if (cur_time + next_t - self.__class__.castedTime) > self.__class__.cooldown + self.__class__.backswing:
            return True

        return False

    def main(self):
        time.sleep(0.1)
        if self.direction != 'up':
            key_down(self.direction)
            time.sleep(0.05)
        if self.jump:
            if self.direction == 'down':
                press(Key.JUMP, 3, down_time=0.1)
            else:
                press(Key.JUMP, 1)
        if self.direction == 'up':
            key_down(self.direction)
            time.sleep(0.2 if self.distance > 32 else 0.4)
            
        cur_time = time.time()
        if (cur_time - self.__class__.castedTime) > self.__class__.cooldown + self.__class__.backswing:
            self.__class__.castedTime = cur_time
            self.__class__.usable_times = 3
        else:
            self.__class__.usable_times -= 1
        press(Key.SHADOW_ASSAULT)
        key_up(self.direction)
        time.sleep(self.backswing)

        
        if settings.record_layout:
            config.layout.add(*config.player_pos)


# 绳索
class RopeLift(Command):
    key = Key.ROPE_LIFT
    cooldown = 3

    def __init__(self, dy: int = 20):
        super().__init__(locals())
        self.dy = abs(dy)

    def main(self):
        if self.dy >= 45:
            press(Key.JUMP, up_time=0.2)
        elif self.dy >= 32:
            press(Key.JUMP, up_time=0.1)
        press(self.__class__.key, up_time=self.dy * 0.07)
        if self.dy >= 32:
            time.sleep((self.dy - 32) * 0.03)

class CruelStab(Command):
    """Attacks using 'CruelStab' in a given direction."""

    def __init__(self, direction, attacks=2, repetitions=1):
        super().__init__(locals())
        self.direction = settings.validate_horizontal_arrows(direction)
        self.attacks = int(attacks)
        self.repetitions = int(repetitions)

    def main(self):
        time.sleep(0.05)
        key_down(self.direction)
        time.sleep(0.05)
        if config.stage_fright and utils.bernoulli(0.7):
            time.sleep(utils.rand_float(0.1, 0.3))
        for _ in range(self.repetitions):
            press(Key.CRUEL_STAB, self.attacks, up_time=0.05)
        key_up(self.direction)
        if self.attacks > 2:
            time.sleep(0.3)
        else:
            time.sleep(0.2)


class MesoExplosion(Command):
    """Uses 'MesoExplosion' once."""

    def main(self):
        press(Key.MESO_EXPLOSION, 1)


class CruelStabRandomDirection(Command):
    """Uses 'CruelStab' once."""
    backswing = 0.3

    def main(self):
        press(Key.CRUEL_STAB, 1, up_time=0.2)
        MesoExplosion().execute()
        time.sleep(self.backswing)


class DarkFlare(Command):
    """
    Uses 'DarkFlare' in a given direction, or towards the center of the map if
    no direction is specified.
    """
    cooldown = 120
    backswing = 0.4

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = settings.validate_horizontal_arrows(direction)

    def main(self):
        if self.direction is None:
            if config.player_pos[0] > 75:
                self.direction = 'left'
            else:
                self.direction = 'right'
                
        press(self.direction)
        press(Key.DARK_FLARE, 2, up_time=self.backswing)


class ShadowVeil(Command):
    """
    Uses 'ShadowVeil' in a given direction, or towards the center of the map if
    no direction is specified.
    """
    backswing = 0.8
    
    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = settings.validate_horizontal_arrows(direction)

    def main(self):
        if self.direction is None:
            if config.player_pos[0] > 75:
                self.direction = 'left'
            else:
                self.direction = 'right'
                
        press(self.direction)
        press(Key.SHADOW_VEIL, 1, up_time=self.backswing)


class ErdaShower(Command):
    """
    Use ErdaShower in a given direction, Placing ErdaFountain if specified. Adds the player's position
    to the current Layout if necessary.
    """
    cooldown = 120
    backswing = 0.8

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = settings.validate_horizontal_arrows(direction)

    def main(self):
        if self.direction:
            press(self.direction)
        key_down('down')
        press(Key.ERDA_SHOWER)
        key_up('down')
        time.sleep(self.backswing)


class SuddenRaid(Command):
    key = Key.SUDDEN_RAID
    cooldown = 30
    backswing = 0.7


class Arachnid(Command):
    key = Key.ARACHNID
    cooldown = 250
    backswing = 0.9


class TrickBlade(Command):
    """
    Uses 'TrickBlade' in a given direction, or towards the center of the map if
    no direction is specified.
    """

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = settings.validate_horizontal_arrows(direction)

    def main(self):
        if self.direction:
            press(self.direction, 1, down_time=0.1, up_time=0.05)
        else:
            if config.player_pos[0] > 0.5:
                press('left', 1, down_time=0.1, up_time=0.05)
            else:
                press('right', 1, down_time=0.1, up_time=0.05)
        press(Key.TRICKBLADE, 3)


class SlashShadowFormation(Command):
    """Uses 'SlashShadowFormation' once."""

    def main(self):
        press(Key.SLASH_SHADOW_FORMATION, 3)


class SonicBlow(Command):
    """Uses 'SonicBlow' once."""

    def main(self):
        press(Key.SONIC_BLOW, 3)


###################
#      Buffs      #
###################

class Buff(Command):
    """Uses each of Shadowers's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.buffs = [GODDESS_BLESSING(),
                      LAST_RESORT(),
                    #   EPIC_ADVENTURE(),
                      MAPLE_WARRIOR(),
                      FOR_THE_GUILD(),
                      HARD_HITTER(),
                      EXP_POTION(),
                      WEALTH_POTION(),
                      GOLD_POTION(),
                      GUILD_POTION(),
                      CANDIED_APPLE(),
                      SHADOW_WALKER(),]

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


class SHADOW_WALKER(Command):
    key = Key.SHADOW_WALKER
    cooldown = 190
    backswing = 0.8


class EPIC_ADVENTURE(Command):
    key = Key.EPIC_ADVENTURE
    cooldown = 120
    backswing = 0.75


class MAPLE_WARRIOR(Command):
    key = Key.MAPLE_WARRIOR
    cooldown = 900
    backswing = 0.75


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
        if SHADOW_WALKER.castedTime != 0 and time.time() - SHADOW_WALKER.castedTime <= 33:
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
        if SHADOW_WALKER.castedTime != 0 and time.time() - SHADOW_WALKER.castedTime <= 33:
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
        if SHADOW_WALKER.castedTime != 0 and time.time() - SHADOW_WALKER.castedTime <= 33:
            return False

        return super().canUse(next_t)


class CANDIED_APPLE(Command):
    key = Key.CANDIED_APPLE
    cooldown = 1800
    backswing = 0

    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Candied Apple')
        if not enabled:
            return False
        if SHADOW_WALKER.castedTime != 0 and time.time() - SHADOW_WALKER.castedTime <= 33:
            return False
        return super().canUse(next_t)
