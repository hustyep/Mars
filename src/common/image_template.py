import cv2
from src.common.dll_helper import dll_helper
from src.common import utils

ASSETS_PATH = 'assets/'

# The rune's buff 
RUNE_BUFF_TEMPLATE = cv2.imread(f'{ASSETS_PATH}rune_buff_template.jpg', 0)
# Alert button
BUTTON_OK_TEMPLATE = cv2.imread(f'{ASSETS_PATH}btn_ok_template.png', 0)
END_TALK_TEMPLATE = cv2.imread(f'{ASSETS_PATH}end_talk_template.png', 0)
# dead alert
DEAD_TOBBSTONE_TEMPLATE = cv2.imread(f'{ASSETS_PATH}dead_tombstone_template.png', 0)
DEAD_OK_TEMPLATE = cv2.imread(f'{ASSETS_PATH}dead_ok_template.png', 0)

BIG_MOUSE_RANGES = (
    ((0, 180, 119), (4, 255, 187)),
    ((0, 255, 17), (0, 255, 153)),
)
# big_mouse = cv2.imread('assets/big_mouse_template.png')
# big_mouse_left = cv2.imread('assets/big_mouse_left_template.png')
# BIG_MOUSE_TEMPLATE = cv2.cvtColor(utils.filter_color(big_mouse, BIG_MOUSE_RANGES), cv2.COLOR_BGR2GRAY)
# BIG_MOUSE_LEFT_TEMPLATE = cv2.cvtColor(utils.filter_color(big_mouse_left, BIG_MOUSE_RANGES), cv2.COLOR_BGR2GRAY)
BIG_MOUSE_TEMPLATE = dll_helper.loadImage('assets/big_mouse_template.png')


# A rune's symbol on the minimap
RUNE_RANGES = (
    ((141, 148, 245), (146, 158, 255)),
)
rune_filtered = utils.filter_color(
    cv2.imread('assets/rune_template.png'), RUNE_RANGES)
RUNE_TEMPLATE = cv2.cvtColor(rune_filtered, cv2.COLOR_BGR2GRAY) # type: ignore

# Other players' symbols on the minimap
OTHER_RANGES = (
    ((0, 245, 215), (10, 255, 255)),
)
other_filtered = utils.filter_color(cv2.imread(
    'assets/other_template.png'), OTHER_RANGES)
OTHER_TEMPLATE = cv2.cvtColor(other_filtered, cv2.COLOR_BGR2GRAY) # type: ignore

# guildmate' symbols on the minimap
GUILDMATE_RANGES = (
    ((120, 40, 180), (120, 110, 255)),
)
guildmate_filtered = utils.filter_color(cv2.imread('assets/guildmate_template.png'), GUILDMATE_RANGES)
GUILDMATE_TEMPLATE = cv2.cvtColor(guildmate_filtered, cv2.COLOR_BGR2GRAY) # type: ignore

# The Elite Boss's warning sign
# ELITE_TEMPLATE = cv2.imread('assets/elite_template.jpg', 0)

# The distance between the top of the minimap and the top of the screen
MINIMAP_TOP_BORDER = 5

# The thickness of the other three borders of the minimap
MINIMAP_BOTTOM_BORDER = 9

# Offset in pixels to adjust for windowed mode
WINDOWED_OFFSET_TOP = 36
WINDOWED_OFFSET_LEFT = 10

# The top-left and bottom-right corners of the minimap
MM_TL_TEMPLATE = cv2.imread('assets/minimap_tl_template.png', 0)
MM_BR_TEMPLATE = cv2.imread('assets/minimap_br_template.png', 0)

MM_TL_BMP = dll_helper.loadImage('assets/minimap_tl.bmp')
MM_BR_BMP = dll_helper.loadImage('assets/minimap_br.bmp')

MMT_HEIGHT = max(MM_TL_TEMPLATE.shape[0], MM_BR_TEMPLATE.shape[0])
MMT_WIDTH = max(MM_TL_TEMPLATE.shape[1], MM_BR_TEMPLATE.shape[1])

# The player's symbol on the minimap
PLAYER_TEMPLATE = cv2.imread('assets/player_template.png', 0)
PT_HEIGHT, PT_WIDTH = PLAYER_TEMPLATE.shape

PLAYER_TEMPLATE_L = cv2.imread('assets/player_template_l.png', 0)

PLAYER_TEMPLATE_R = cv2.imread('assets/player_template_r.png', 0)

GREEN_RANGES = (
        ((50, 200, 46), (77, 255, 255)),
)
RED_RANGES = (
    ((0, 43, 46), (10, 255, 255)),
    ((156, 43, 46), (180, 255, 255)),
)
YELLOW_RANGES = (
    ((26, 43, 46), (34, 255, 255)),
)
WHITE_RANGES = (
    ((0, 0, 150), (180, 30, 255)),
)
BLUE_RANGES = (
    ((100, 43, 46), (124, 255, 255)),
)
GRAY_RANGES = (
    ((0, 0, 46), (180, 43, 220)),
)