import threading
import time
import datetime
from enum import Enum
import cv2
import pytesseract as tess
import numpy as np
import mss
import mss.windows

if __name__ != "__main__":
    from src.common import utils, config
    from src.modules.capture import capture
    from src.modules.notifier import notifier
    from src.modules.chat_bot import chat_bot
    from src.common.constants import *

NORMAL_MSG_RANGES = (
    ((0, 0, 150), (180, 30, 255)),
)

WORLD_MSG_RANGES = (
    ((30, 200, 100), (80, 255, 255)),
)


class GameMsgType(Enum):
    NORMAL = 'normal'
    WORLD = 'world'
    SYSTEM = 'system'
    BATTLE = 'battle'
    MVP = 'MVP'


class GameMsg:

    def __init__(self, text: str, type: GameMsgType, image) -> None:
        self.type = type
        self.text = text
        self.image = image
        self.timestamp = time.time()

        # MPV Msg
        self.channel = 0
        self.time = None
        self.map = None

    def equal(self, other) -> bool:
        if other is None:
            return False
        if self.type != other.type:
            return False
        return self.text == other.text


class ChatCapture:

    def __init__(self):
        super().__init__()
        self.sct = mss.mss()

        self.last_nomarl_msg = None
        self.last_mvp_msg = None

        self.ready = False
        self.thread = threading.Thread(target=self._main)
        self.thread.daemon = True

    def start(self):
        """Starts this Chat Capture's thread."""

        print('\n[~] Started chat capture')
        self.thread.start()

    def _main(self):
        self.ready = True
        mss.windows.CAPTUREBLT = 0

        with mss.mss() as self.sct:
            while True:
                window = {
                    'left': capture.window['left'] + capture.window['width'] + 5,
                    'top': capture.window['top'],
                    'width': 400,
                    'height': capture.window["height"],
                }

                frame = self.screenshot(window)
                # cv2.imshow("", frame)
                # cv2.waitKey(0)
                if frame is not None:
                    new_normal_msg = self.get_new_msg(frame, GameMsgType.NORMAL)
                    if new_normal_msg and not new_normal_msg.equal(self.last_nomarl_msg):
                        self.last_nomarl_msg = new_normal_msg
                        self.notify_new_msg(new_normal_msg)

                    new_mvp_msg = self.get_new_msg(frame, GameMsgType.MVP)
                    if new_mvp_msg and not new_mvp_msg.equal(self.last_mvp_msg):
                        self.last_mvp_msg = new_mvp_msg
                        self.notify_new_msg(new_mvp_msg)

                time.sleep(0.5)

    def screenshot(self, window, delay=1):
        try:
            return np.array(self.sct.grab(window))
        except mss.exception.ScreenShotError:
            print(f'\n[!] Error while taking screenshot, retrying in {delay} second'
                  + ('s' if delay != 1 else ''))
            time.sleep(delay)

    def get_new_msg(self, image, msg_type) -> GameMsg | None:
        if msg_type == GameMsgType.NORMAL:
            image = image[-70:-29, 2:400]
            msg_list = self.image_to_str(image)
        else:
            image = image[-540:-440, 2:400]
            msg_list = self.image_to_str(image)
            # image = image[-567:-518, 2:400]
            # cv2.imshow("", image)
            # cv2.waitKey(0)
        if len(msg_list) == 0:
            return None
        new_msg = msg_list.pop()
        if msg_type == GameMsgType.MVP:
            return self.get_mpv_msg(new_msg, image)

        return GameMsg(new_msg, msg_type, image)

    def get_mpv_msg(self, text, image) -> GameMsg | None:
        print(text)
        low_text = text.lower()
        if 'mvp' in low_text and 'x' in low_text:
            mvp_msg = GameMsg(text, GameMsgType.MVP, image)
            list = low_text.split(" ")
            min_str = ''
            channel = 0
            for words in list:
                if not min_str:
                    if words.startswith("xx:"):
                        min_str = words[3:]
                    elif words.startswith('xx') or words.startswith('x:'):
                        min_str = words[2:]
                    # elif words.startswith('x'):
                    #     min_str = words[1:]

                if channel == 0:
                    tmp = 0
                    if words.startswith('ch') or words.startswith('cc'):
                        try:
                            tmp = int(words[2:4])
                        except Exception as e:
                            try:
                                tmp = int(words[2:3])
                            except Exception as e:
                                pass
                    elif words.startswith('c'):
                        try:
                            tmp = int(words[1:3])
                        except Exception as e:
                            try:
                                tmp = int(words[1:2])
                            except Exception as e:
                                pass
                    if tmp and tmp <= 40:
                        channel = tmp
                        
                if 'ms' in words or 'shrine' in words or 'mushroom' in words:
                    mvp_msg.map = 'mushroom shrine'

            mvp_msg.channel = channel

            if min_str:
                min = int(min_str)
                hour = 0
                if min >= 0 and min <= 59:
                    cur_hour = int(low_text[1:3])
                    cur_min = int(low_text[4:6])
                    # cur_hour = datetime.datetime.now().hour
                    # cur_min = datetime.datetime.now().minute
                    if min >= cur_min:
                        hour = cur_hour
                    else:
                        hour = (cur_hour + 1) % 24
                    mvp_msg.time = f'{hour}:{min}'

            return mvp_msg
        else:
            return None

    def notify_new_msg(self, msg: GameMsg):
        text = f'{"🏆" if msg.type == GameMsgType.MVP else "💬"}{msg.text}'
        print(text)
        if (BotFatal.WHITE_ROOM in notifier.notice_time_record and notifier.notice_time_record[BotFatal.WHITE_ROOM] > 0) or config.notice_level >= 4:
            path = 'screenshot/msgs'
            image_path = utils.save_screenshot(
                frame=msg.image, file_path=path, compress=False)
            chat_bot.send_message(text=text, image_path=image_path)

    def image_to_str(self, image, ranges=None):
        if ranges:
            image = utils.filter_color(image, ranges)
        # cv2.imshow("", image)
        # cv2.waitKey(0)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        text = tess.image_to_string(image_rgb, lang="eng")
        content = text.replace("\f", "").split("\n")

        list = []
        for item in content:
            if len(item.strip()) == 0:
                continue
            if item.startswith('[') and len(item) > 6 and item[6] == ']':
                list.append(item)
            elif len(list) > 0:
                new = list.pop() + item
                list.append(new)

        return list


chat_capture = ChatCapture()


if __name__ == "__main__":
    YELLOW_RANGES = (
        ((26, 43, 46), (34, 255, 255)),
    )
    BLUE_RANGES = (
        ((100, 43, 46), (124, 255, 255)),
    )
    GREEN_RANGES = (
        ((50, 200, 46), (77, 255, 255)),
    )
    WORLD_MSG_RANGES = (
        ((30, 200, 100), (80, 255, 255)),
    )
    WHITE_RANGES = (
        # ((0, 0, 100), (180, 50, 255)),
        ((0, 0, 150), (180, 30, 255)),
    )
    image = cv2.imread(".test/3.png")
    # image = image[-64:-29, 2:400]
    # image = image[-500:-439, 2:400]
    # text = chat_capture.image_to_str(image)
    msg = chat_capture.get_new_msg(image, GameMsgType.MVP)
    print(msg.text)
    while True:
        new_msg = chat_capture.get_new_msg(image, GameMsgType.MVP)
        if new_msg and not new_msg.equal(msg):
            print("New Msg")
        time.sleep(0.5)
