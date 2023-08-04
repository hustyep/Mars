from abc import ABC, abstractmethod
import time
from src.common.vkeys import press

class Skill(ABC):
    def __init__(self):
        self.key = None
        self.cooldown = 0
        self.castedTime = None
        self.precast = None
        self.backswing = 500

    def canUse(self, next_t: float = 0) -> bool:
        if self.cooldown is None:
            return True

        cur_time = time.time()
        if (cur_time + next_t - self.castedTime) > self.cooldown + self.backswing:
            return True

        return False
    
    def cast(self):
        if not self.canUse():
            return
        
        print(f"cast skill: {self.key}")
        time.sleep(self.precast)
        self.castedTime = time.time()
        press(self.key)
        time.sleep(self.backswing)

    @abstractmethod
    def sound(self):
        pass

    def eat(self, food):
        print("{} is eating {}".format(self.name, food))
