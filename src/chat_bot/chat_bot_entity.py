
from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum

class ChatBotCommand(Enum):
    START = "start"
    PAUSE = 'pause'
    INFO = 'info'
    SCREENSHOT = 'screenshot'
    PRINTSCREEN = 'printscreen'
    LEVEL = 'level'
    CLICK = 'click'
    SAY = 'say'
    TP = 'tp'
    CHANGE_CHANNEL = 'cc'

class ChatBotEntity(ABC):
    
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def send_text(self, message: str, retry=0):
        pass
    
    @abstractmethod
    def send_image(self, image_path, caption=None, retry=0):
        pass
    
    @abstractmethod
    def send_message(self, text=None, image_path=None, retry=0):
        pass