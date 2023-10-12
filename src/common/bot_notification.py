from enum import Enum, auto

class BotFatal(Enum):
    WHITE_ROOM = 'White Room'
    CRASH = 'Crash'
    
class BotError(Enum):
    DEAD = 'Dead'
    LOST_WINDOW = 'Lost Window'
    LOST_MINI_MAP = 'Lost Minimap'
    LOST_PLAYER = 'Lost Player'
    BLACK_SCREEN = 'Black Screen'
    NO_MOVEMENT = 'No Movement'
    RUNE_ERROR = 'Rune Error'
    OTHERS_STAY_OVER_120S = 'Someone stay over 120s'
        
class BotWarnning(Enum):
    RUNE_FAILED = 'Rune Failed'
    OTHERS_COMMING = 'Someone\'s comming'
    OTHERS_STAY_OVER_30S = 'Someone stay over 30s'
    OTHERS_STAY_OVER_60S = 'Someone stay over 60s'
    BINDED = 'Binded'

class BotInfo(Enum):
    RUNE_ACTIVE = 'Rune Active'
    RUNE_LIBERATED = 'Rune Liberated'
    OTHERS_LEAVED = 'Someone\'s gone'
    MINE_ACTIVE = 'Mine Active'
    BOSS_APPEAR = 'Boss Appear'
    
class BotDebug(Enum):
    SCREENSHOT_FAILED = 'Screenshot Failed'
    CALIBRATED = auto()
    PLAYER_LOCATION_UPDATE = auto()
