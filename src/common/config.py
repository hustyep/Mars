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

# Shares the main bot loop
bot = None

# Shares the video capture loop
capture = None

# Shares the keyboard listener
listener = None

# Shares the gui to all modules
gui = None

# Shares the usb dll
usb = None

# Shares the tool dll
dllTool = None  

notifier = None