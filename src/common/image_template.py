import cv2
from src.common.dll_helper import dll_helper
from src.common import utils

ASSETS_PATH = 'assets/'

# The rune's buff 
RUNE_BUFF_TEMPLATE = cv2.imread(f'{ASSETS_PATH}rune/rune_buff_template.jpg', 0)
RUNE_BUFF_GRAY_TEMPLATE = cv2.imread(f'{ASSETS_PATH}rune/rune_buff_gray_template.png', 0)

########################
#      exceptions      #
########################

# Alert button
BUTTON_OK_TEMPLATE = cv2.imread(f'{ASSETS_PATH}exceptions/btn_ok_template.png', 0)
END_TALK_TEMPLATE = cv2.imread(f'{ASSETS_PATH}exceptions/end_talk_template.png', 0)
# dead alert
DEAD_TOBBSTONE_TEMPLATE = cv2.imread(f'{ASSETS_PATH}exceptions/dead_tombstone_template.png', 0)
DEAD_OK_TEMPLATE = cv2.imread(f'{ASSETS_PATH}exceptions/dead_ok_template.png', 0)

SKULL_TEMPLATE = cv2.imread(f'{ASSETS_PATH}exceptions/skull_template.png', 0)

# The Elite Boss's warning sign
ELITE_TEMPLATE = cv2.imread(f'{ASSETS_PATH}exceptions/elite_template.jpg', 0)

# White Room
WHITE_ROOM_TEMPLATE = cv2.imread(f'{ASSETS_PATH}exceptions/white_room_template.png', 0)

WECHAT_CALL_TEMPLATE = cv2.imread(f'{ASSETS_PATH}exceptions/wechat_call.png', 0)
WECHAT_CALL_TEMPLATE_2X = cv2.imread(f'{ASSETS_PATH}exceptions/wechat_call@2x.png', 0)

#####################
#      mineral      #
#####################

MINAL_HEART_TEMPLATE = cv2.imread('assets/mineral/mineral_heart_template.png', 0)
HERB_YELLOW_TEMPLATE = cv2.imread('assets/mineral/herb_yellow_template.png', 0)
HERB_PURPLE_TEMPLATE = cv2.imread('assets/mineral/herb_purple_template.png', 0)
MINAL_CRYSTAL_TEMPLATE = cv2.imread('assets/mineral/mineral_crystal_template.png', 0)

####################
#     minimap      #
####################

# A rune's symbol on the minimap
RUNE_RANGES = (
    ((141, 148, 245), (146, 158, 255)),
)
rune_filtered = utils.filter_color(
    cv2.imread(f'{ASSETS_PATH}minimap/minimap_rune_template.png'), RUNE_RANGES)
RUNE_TEMPLATE = cv2.cvtColor(rune_filtered, cv2.COLOR_BGR2GRAY) # type: ignore

# Other players' symbols on the minimap
OTHER_RANGES = (
    ((0, 245, 215), (10, 255, 255)),
)
other_filtered = utils.filter_color(cv2.imread(
    f'{ASSETS_PATH}minimap/minimap_other_template.png'), OTHER_RANGES)
OTHER_TEMPLATE = cv2.cvtColor(other_filtered, cv2.COLOR_BGR2GRAY)

# guildmate' symbols on the minimap
GUILDMATE_RANGES = (
    ((120, 40, 180), (120, 110, 255)),
)
guildmate_filtered = utils.filter_color(cv2.imread(f'{ASSETS_PATH}minimap/minimap_guildmate_template.png'), GUILDMATE_RANGES)
GUILDMATE_TEMPLATE = cv2.cvtColor(guildmate_filtered, cv2.COLOR_BGR2GRAY)

# Offset in pixels to adjust for windowed mode
WINDOWED_OFFSET_TOP = 36
WINDOWED_OFFSET_LEFT = 10

# The top-left and bottom-right corners of the minimap
MM_TL_BMP = dll_helper.loadImage(f'{ASSETS_PATH}minimap/minimap_border_tl.bmp')
MM_BR_BMP = dll_helper.loadImage(f'{ASSETS_PATH}minimap/minimap_border_br.bmp')

# The player's symbol on the minimap
PLAYER_TEMPLATE = cv2.imread(f'{ASSETS_PATH}minimap/minimap_player_template.png', 0)
PLAYER_TEMPLATE_L = cv2.imread(f'{ASSETS_PATH}minimap/minimap_player_template_l.png', 0)
PLAYER_TEMPLATE_R = cv2.imread(f'{ASSETS_PATH}minimap/minimap_player_template_r.png', 0)


###########################
#      common ranges      #
###########################

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
ORANGE_RANGES = (
    ((11, 43, 46), (25, 255, 255)),
)

# https://blog.csdn.net/weixin_45946270/article/details/124827045
