import tkinter as tk
from src.gui.interfaces import LabelFrame, Frame
from src.common.interfaces import Configurable


class Buffs(LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'Buffs', **kwargs)

        self.buff_settings = BuffSettings('buffs')

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
                variable= value,
                text=k,
                command=self._on_change
            )
            check.grid(row=index // 2, column= index % 2, sticky=tk.W, padx=(index % 2) * 50)
            index += 1
            self.check_boxes.append(check)
            self.check_values.append(value)
                
                
    def _on_change(self):
        for i in range(len(self.check_boxes)):
            check = self.check_boxes[i]
            value = self.check_values[i]
            self.buff_settings.set(check.cget('text'), value.get())
        self.buff_settings.save_config()

class BuffSettings(Configurable):
    DEFAULT_CONFIG = {
        'Guild Buff': False,
        'Guild Potion': False,
        'Exp Potion': False,
        'Wealthy Potion': False,
        'Gold Potion': False,
        'Candied Apple': False,
        'Legion Wealthy': False,
        'Exp Coupon': False
    }

    def get(self, key):
        return self.config[key]

    def set(self, key, value):
        assert key in self.config
        self.config[key] = value