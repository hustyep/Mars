"""A collection of all commands that Shadower can use to interact with the game. 	"""

from src.common import config, settings, utils
import time
import math
import threading
from src.routine.components import Command, Detect_Mobs, direction_changed, sleep_while_move_y, sleep_before_y
from src.common.vkeys import press, key_down, key_up, releaseAll

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
    GOLD_POTION = '='
    GUILD_POTION = "9"
    CANDIED_APPLE = '5'
    LEGION_WEALTHY = ''
    EXP_COUPON = '6'

    # Skills
    CRUEL_STAB = 'f'
    MESO_EXPLOSION = 'd'
    SUDDEN_RAID = 'r'
    DARK_FLARE = 'w'
    SHADOW_VEIL = 'x'
    ARACHNID = 'j'
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

    if config.elite_boss_detected:
        config.elite_boss_detected = False
        SlashShadowFormation().execute()

    if config.stage_fright and direction != 'up' and utils.bernoulli(0.75):
        time.sleep(utils.rand_float(0.1, 0.3))
    d_x = target[0] - config.player_pos[0]
    d_y = target[1] - config.player_pos[1]
    if direction == "up":
        MoveUp(dy=abs(d_y)).execute()
    elif direction == "down":
        MoveDown(dy=abs(d_y)).execute()
    elif abs(d_y) >= 26 and abs(d_x) >= 24 and ShadowAssault.usable_count() > 2:
        ShadowAssault(dx=d_x, dy=d_y).execute()
    elif abs(d_x) >= 24:
        HitAndRun(direction, target).execute()
    else:
        time.sleep(0.05)
        
def detect_elite(direction):
    if direction == 'right':
        has_elite = Detect_Mobs(top=150,bottom=-50,left=-300,right=900,isElite=True).execute()
    else:
        has_elite = Detect_Mobs(top=150,bottom=-50,left=900,right=-300,isElite=True).execute()
    config.elite_detected = has_elite is not None and len(has_elite) > 0
        
class HitAndRun(Command):
    def __init__(self, direction, target):
        super().__init__(locals())
        self.direction = direction
        self.target = target

    def main(self):
        d_x = self.target[0] - config.player_pos[0]
        if config.mob_detect:
            if direction_changed():
                print("direction_changed")
                time.sleep(0.08)
                key_up(self.direction)
                time.sleep(0.9)
                has_elite = Detect_Mobs(top=200,bottom=-50,left=300,right=300,isElite=True).execute()
                if has_elite is not None and len(has_elite) > 0:
                    SonicBlow().execute()
                mobs = Detect_Mobs(top=30*15,bottom=15*15,left=80*15,right=80*15).execute()
                count = 0
                while count < 500 and mobs is not None and len(mobs) < 2:
                    count += 1
                    time.sleep(0.01)
                    mobs = Detect_Mobs(top=300,bottom=100,left=80*15,right=80*15).execute()
                key_down(self.direction)
            
            threading.Thread(target=detect_elite, args=(self.direction,)).start()
            FlashJump(dx=abs(d_x)).execute()
            CruelStabRandomDirection().execute()
            # sleep_before_y(target_y=self.target[1], tolorance=1)
            sleep_while_move_y(interval=0.017, n=5)
            if config.elite_detected:
                SonicBlow().execute()
        else:
            FlashJump(dx=abs(d_x)).execute()
            CruelStabRandomDirection().execute()
            sleep_before_y(target_y=self.target[1])
            

#########################
#        Y轴移动         #
#########################

class MoveUp(Command):
    def __init__(self, dy: int = 20):
        super().__init__(locals())
        self.dy = abs(dy)

    def main(self):
        self.print_debug_info()

        if self.dy <= 6:
            press(Key.JUMP)
            sleep_while_move_y()
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
        self.print_debug_info()

        if self.dy >= 25 and ShadowAssault.usable_count() >= 3:
            ShadowAssault(direction='down', jump='True',
                          distance=self.dy).execute()
        else:
            key_down('down')
            press(Key.JUMP, 1, down_time=0.2, up_time=0.2)
            key_up('down')
            sleep_while_move_y()
            # time.sleep(0.8 if self.dy >= 15 else 0.7)


class JumpUp(Command):
    def __init__(self, dy: int = 20):
        super().__init__(locals())
        self.dy = abs(dy)

    def main(self):
        self.print_debug_info()

        time.sleep(0.5)
        press(Key.JUMP)
        key_down('up')
        time.sleep(0.06 if self.dy >= 20 else 0.1)
        press(Key.FLASH_JUMP, 1)
        key_up('up')
        sleep_while_move_y(interval=0.05, n=6)
        # time.sleep(1.5)


class FlashJump(Command):
    """Performs a flash jump in the given direction."""

    def __init__(self, time=1, dx=None):
        super().__init__(locals())

        if dx is not None:
            self.time = 2 if dx <= 32 else 2
        else:
            self.time = time

    def main(self):
        self.print_debug_info()

        if self.time == 1:
            press(Key.JUMP, 1, down_time=0.05, up_time=0.05)
        else:
            press(Key.JUMP, 1, down_time=0.03, up_time=0.03)
        press(Key.FLASH_JUMP, self.time, down_time=0.03, up_time=0.03)


class ShadowAssault(Command):
    """
    ShadowAssault in a given direction, jumping if specified. Adds the player's position
    to the current Layout if necessary.
    """

    backswing = 0.15
    usable_times = 4
    cooldown = 60

    def __init__(self, direction='up', jump='True', distance=80, dx=None, dy=None):
        super().__init__(locals())
        if dx is None or dy is None:
            self.direction = direction
            self.jump = settings.validate_boolean(jump)
            self.distance = settings.validate_nonnegative_int(distance)
        else:
            if dy < 0 and dx < 0:
                self.direction = 'upleft'
                self.jump = True
            elif dy < 0 and dx > 0:
                self.direction = 'upright'
                self.jump = True
            elif dy > 0 and dx < 0:
                self.direction = 'downleft'
                self.jump = True
            elif dy > 0 and dx > 0:
                self.direction = 'downright'
                self.jump = True
            elif dy != 0:
                self.direction = 'up' if dy < 0 else 'down'
                self.jump = True
            elif dx != 0:
                self.direction = 'left' if dx < 0 else 'right'
                self.jump = False
            else:
                self.direction = direction
                self.jump = settings.validate_boolean(jump)
            self.distance = math.sqrt(dx ** 2 + dy ** 2)

    @staticmethod
    def usable_count():
        if (time.time() - ShadowAssault.castedTime) > ShadowAssault.cooldown + ShadowAssault.backswing:
            return 4
        else:
            return ShadowAssault.usable_times

    def canUse(self, next_t: float = 0) -> bool:

        if self.__class__.usable_times > 0:
            return True

        cur_time = time.time()
        if (cur_time + next_t - self.__class__.castedTime) > self.__class__.cooldown + self.__class__.backswing:
            return True

        return False

    def main(self):
        self.print_debug_info()

        if self.distance == 0:
            return

        time.sleep(0.2)

        if self.direction.endswith('left'):
            if config.player_direction != 'left':
                press('left', down_time=0.1)
        elif self.direction.endswith("right"):
            if config.player_direction != 'right':
                press("right", down_time=0.1)
        if self.jump:
            if self.direction.startswith('down'):
                key_down('down')
                press(Key.JUMP, 1, down_time=0.2, up_time=0.2)
                key_up("down")
            else:
                press(Key.JUMP)
                time.sleep(0.1 if self.distance > 32 else 0.4)

        key_down(self.direction)
        time.sleep(0.05)

        cur_time = time.time()
        if (cur_time - self.__class__.castedTime) > self.__class__.cooldown + self.__class__.backswing:
            self.__class__.castedTime = cur_time
            self.__class__.usable_times = 3
        else:
            self.__class__.usable_times -= 1
        press(Key.SHADOW_ASSAULT)
        key_up(self.direction)
        time.sleep(self.backswing)
        sleep_while_move_y(interval=0.04)
        
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
        self.print_debug_info()

        if self.dy >= 45:
            press(Key.JUMP, up_time=0.2)
        elif self.dy >= 32:
            press(Key.JUMP, up_time=0.1)
        press(self.__class__.key)
        sleep_while_move_y(interval=0.05, n=6)
        # press(self.__class__.key, up_time=self.dy * 0.07)
        # if self.dy >= 32:
        #     time.sleep((self.dy - 32) * 0.01)


class CruelStab(Command):
    """Attacks using 'CruelStab' in a given direction."""

    def __init__(self, direction, attacks=2, repetitions=1):
        super().__init__(locals())
        self.direction = settings.validate_horizontal_arrows(direction)
        self.attacks = int(attacks)
        self.repetitions = int(repetitions)

    def main(self):
        self.print_debug_info()

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


#########################
#         Skills        #
#########################

class MesoExplosion(Command):
    """Uses 'MesoExplosion' once."""

    def main(self):
        press(Key.MESO_EXPLOSION)


class CruelStabRandomDirection(Command):
    """Uses 'CruelStab' once."""
    backswing = 0.1

    def main(self):
        press(Key.CRUEL_STAB, 1, up_time=0.2)
        MesoExplosion().execute()
        time.sleep(self.backswing)


class DarkFlare(Command):
    """
    Uses 'DarkFlare' in a given direction, or towards the center of the map if
    no direction is specified.
    """
    cooldown = 57
    backswing = 0.8
    key = Key.DARK_FLARE

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = settings.validate_horizontal_arrows(direction)

    def main(self):
        self.print_debug_info()
        
        while not self.canUse():
            time.sleep(0.1)
        if self.direction is None:
            if config.player_pos[0] > 75:
                self.direction = 'left'
            else:
                self.direction = 'right'

        press(self.direction)
        press(Key.DARK_FLARE, 1, up_time=self.backswing)
        # self.__class__.castedTime = time.time()


class ShadowVeil(Command):
    key = Key.SHADOW_VEIL
    cooldown = 57
    precast = 0.3
    backswing = 0.9

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = settings.validate_horizontal_arrows(direction)

    def main(self):
        self.print_debug_info()
        if self.direction is not None:
            press(self.direction)
        super().main()


class ErdaShower(Command):
    key = Key.ERDA_SHOWER
    cooldown = 58
    backswing = 0.8

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = settings.validate_horizontal_arrows(direction)

    def main(self):
        while not self.canUse():
            time.sleep(0.1)
        self.print_debug_info()
        if self.direction:
            press(self.direction)
        key_down('down')
        press(Key.ERDA_SHOWER)
        key_up('down')
        self.__class__.castedTime = time.time()
        time.sleep(self.backswing)


class SuddenRaid(Command):
    key = Key.SUDDEN_RAID
    cooldown = 30
    backswing = 0.7

    def canUse(self, next_t: float = 0) -> bool:
        usable = super().canUse(next_t)
        if usable:
            mobs = Detect_Mobs(top=500,bottom=500,left=500,right=500,debug=False).execute()
            return mobs is None or len(mobs) > 0
        else:
            return False
            

class Arachnid(Command):
    key = Key.ARACHNID
    cooldown = 250
    backswing = 0.9


class TrickBlade(Command):
    key = Key.TRICKBLADE
    cooldown = 14
    backswing = 0.9

    def __init__(self, direction=None):
        super().__init__(locals())
        if direction is None:
            self.direction = direction
        else:
            self.direction = settings.validate_horizontal_arrows(direction)
            
    def canUse(self, next_t: float = 0) -> bool:
        usable = super().canUse(next_t)
        if usable:
            mobs = Detect_Mobs(top=200,bottom=100,left=300,right=300).execute()
            return mobs is None or len(mobs) > 0
        else:
            return False


class SlashShadowFormation(Command):
    key = Key.SLASH_SHADOW_FORMATION
    cooldown = 90
    backswing = 0.8

class SonicBlow(Command):
    key = Key.SONIC_BLOW
    cooldown = 45
    backswing = 3


###################
#      Buffs      #
###################

class Buff(Command):
    """Uses each of Shadowers's buffs once."""

    def __init__(self):
        super().__init__(locals())
        self.buffs = [
            MAPLE_WARRIOR,
            GODDESS_BLESSING,
            LAST_RESORT,
            FOR_THE_GUILD,
            HARD_HITTER,
            SHADOW_WALKER,
        ]

    def main(self):
        for buff in self.buffs:
            if buff().canUse():
                buff().execute()
                break


class GODDESS_BLESSING(Command):
    key = Key.GODDESS_BLESSING
    cooldown = 180
    precast = 0.3
    backswing = 0.9


class LAST_RESORT(Command):
    key = Key.LAST_RESORT
    cooldown = 75
    precast = 0.3
    backswing = 0.8


class SHADOW_WALKER(Command):
    key = Key.SHADOW_WALKER
    cooldown = 180
    precast = 0.3
    backswing = 0.8

    def main(self):
        super().main()
        config.hide_start = time.time()


class EPIC_ADVENTURE(Command):
    key = Key.EPIC_ADVENTURE
    cooldown = 120
    backswing = 0.75


class MAPLE_WARRIOR(Command):
    key = Key.MAPLE_WARRIOR
    cooldown = 900
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


###################
#      Potion     #
###################

class Potion(Command):
    """Uses each of Shadowers's potion once."""

    def __init__(self):
        super().__init__(locals())
        self.potions = [
            GOLD_POTION,
            CANDIED_APPLE,
            GUILD_POTION,
            LEGION_WEALTHY,
            EXP_COUPON,
            EXP_POTION,
            WEALTH_POTION,
        ]

    def main(self):
        if SHADOW_WALKER.castedTime != 0 and time.time() - SHADOW_WALKER.castedTime <= 35:
            return
        for potion in self.potions:
            if potion().canUse():
                potion().execute()


class EXP_POTION(Command):
    key = Key.EXP_POTION
    cooldown = 7250
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Exp Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class WEALTH_POTION(Command):
    key = Key.WEALTH_POTION
    cooldown = 7250
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Wealthy Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class GOLD_POTION(Command):
    key = Key.GOLD_POTION
    cooldown = 1810
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Gold Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class GUILD_POTION(Command):
    key = Key.GUILD_POTION
    cooldown = 1810
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Guild Potion')
        if not enabled:
            return False
        return super().canUse(next_t)


class CANDIED_APPLE(Command):
    key = Key.CANDIED_APPLE
    cooldown = 1800
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Candied Apple')
        if not enabled:
            return False
        return super().canUse(next_t)


class LEGION_WEALTHY(Command):
    key = Key.LEGION_WEALTHY
    cooldown = 1810
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Legion Wealthy')
        if not enabled:
            return False
        return super().canUse(next_t)


class EXP_COUPON(Command):
    key = Key.EXP_COUPON
    cooldown = 1810
    backswing = 0.5

    def canUse(self, next_t: float = 0) -> bool:
        enabled = config.gui.settings.buffs.buff_settings.get('Exp Coupon')
        if not enabled:
            return False
        return super().canUse(next_t)
