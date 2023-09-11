"""A collection of variables shared across multiple modules."""

#########################
#       Constants       #
#########################
RESOURCES_DIR = 'resources'


#################################
#       Global Variables        #
#################################
# The player's position relative to the minimap
player_pos = (0, 0)

# Describes whether the main bot loop is currently running or not
enabled: bool = False

# If there is another player in the map, Mars will purposely make random human-like mistakes
stage_fright = False

# Represents the current shortest path that the bot is taking
path = []

################################
#       Notifier Config        #
################################

wechat_name = 'yep'

# 填写真实的发邮件服务器用户名、密码
mail_user = 'mars_maple@163.com'
mail_password = 'KQJKXCWSVPGOWPEW'
# 实际发给的收件人
mail_to_addrs = '326143583@qq.com'

telegram_apiToken = '6683915847:AAH1iOECS1y394jkvDCD2YhHLxIDIAmGGac'
# telegram_apiToken = '6497654972:AAExWRJvmuswPb2MzbtHi8fIp140TdeDSQM'

telegram_chat_id = '805381440'

#############################
#       Shared Modules      #
#############################
# A Routine object that manages the 'machine code' of the current routine
routine = None

# Stores the Layout object associated with the current routine
layout = None

# Shares the gui to all modules
gui = None


file_setting = None

command_book = None

# Rune status
rune_active = False
rune_pos = None
rune_closest_pos = None

# Bot status
started_time = None
notice_level = 1
default_notice_interval = 30
global_keys = None

# change channel
change_channel = False
lost_minimap = True