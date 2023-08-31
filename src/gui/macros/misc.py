import tkinter as tk
import keyboard
import time
import threading
from src.common.action_simulator import ActionSimulator as sim

from src.gui.interfaces import LabelFrame, Frame
from src.common.interfaces import Configurable

class Misc(LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'Misc(ctrl+shift+y)', **kwargs)
        
        self.running = False
        
        # 使用keyboard库注册热键
        keyboard.add_hotkey('ctrl+shift+y', self.hotkey_pressed)

        self.buff_settings = MiscSettings('macros_misc')

        buff_row = Frame(self)
        buff_row.pack(side=tk.TOP, expand=True, pady=5, padx=5)

        index = 0
        self.check_boxes = []
        self.check_values = []
        for k, v in self.buff_settings.config.items():
            try:
                value = tk.BooleanVar(value=v)
            except Exception as e:
                value = tk.BooleanVar(value=False)
            check = tk.Checkbutton(
                buff_row,
                variable=value,
                text=k,
                command=self._on_change
            )
            check.grid(row=index // 2, column=index % 2,
                       sticky=tk.W, padx=(index % 2) * 50)
            index += 1
            self.check_boxes.append(check)
            self.check_values.append(value)

    def _on_change(self):
        for i in range(len(self.check_boxes)):
            check = self.check_boxes[i]
            value = self.check_values[i]
            self.buff_settings.set(check.cget('text'), value.get())
        self.buff_settings.save_config()

    # 定义一个在按下热键时将被执行的函数
    def hotkey_pressed(self):
        self.running = not self.running
        print(f"hotkey被按下！ {self.running}")
        time.sleep(0.5)
        
        if self.running:
            self.run_macro()
    
    def run_macro(self):
        for index in range(len(self.check_values)):
            value = self.check_values[index]
            if value.get():
                threading.Thread(target=self.run, args=(index,)).start()
                break
                
    def run(self, macro_index):
        match (macro_index):
            case 0:
                self.open_herb()
            case 1:
                self.open_herb()
            case 2:
                self.reset_potential()
    
    def reset_potential(self):
        while(self.running):
            sim.mouse_left_click()
            sim.click_key('enter')
            sim.click_key('enter')
            sim.click_key('enter')
            
            

class MiscSettings(Configurable):
    DEFAULT_CONFIG = {
        'Open Herb': False,
        'Open Mineral': False,
        'Cube': False,
        'Star': False,
    }

    def get(self, key):
        return self.config[key]

    def set(self, key, value):
        assert key in self.config
        self.config[key] = value
