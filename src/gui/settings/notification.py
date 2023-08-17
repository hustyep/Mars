import tkinter as tk
from src.gui.interfaces import LabelFrame, Frame
from src.common.interfaces import Configurable
import threading
from src.common import config

class Notification(LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'Crontab', **kwargs)
        
        self.time_to_stop = 0
        self.time_to_start = 0
        
        self.stop_timer: threading.Timer = None
        self.start_schedule: threading.Timer = None
        self.schedule_running = False

        self.pet_settings = PetSettings('pets')
        self.auto_feed = tk.BooleanVar(
            value=self.pet_settings.get('Auto-feed'))
        self.num_pets = tk.IntVar(value=self.pet_settings.get('Num pets'))

        # 定时任务
        delay_row = Frame(self)
        delay_row.pack(side=tk.TOP, fill='x', expand=True, pady=(0, 5), padx=5)
        
        label = tk.Label(delay_row, text='Time to stop:')
        label.pack(side=tk.LEFT, padx=(0, 15))
        
        display_var = tk.StringVar(value='60:00')
        self.stop_entry = tk.Entry(delay_row,
                         validate='key',
                         textvariable = display_var,
                         takefocus=False)
        self.stop_entry.pack(side=tk.LEFT, padx=(0, 15))
        
        self.stop_btn = tk.Button(delay_row, text='setup', command=self._on_time_to_stop)
        self.stop_btn.pack(side=tk.LEFT,)
        
        
        
        num_row = Frame(self)
        num_row.pack(side=tk.TOP, fill='x', expand=True, pady=(0, 5), padx=5)
        label = tk.Label(num_row, text='Number of pets to feed:')
        label.pack(side=tk.LEFT, padx=(0, 15))
        radio_group = Frame(num_row)
        radio_group.pack(side=tk.LEFT)
        for i in range(1, 4):
            radio = tk.Radiobutton(
                radio_group,
                text=str(i),
                variable=self.num_pets,
                value=i,
                command=self._on_change
            )
            radio.pack(side=tk.LEFT, padx=(0, 10))

    def _on_change(self):
        self.pet_settings.set('Auto-feed', self.auto_feed.get())
        self.pet_settings.set('Num pets', self.num_pets.get())
        self.pet_settings.save_config()
        
    
    def _on_time_to_stop(self):
        if self.stop_btn.cget('text') == "setup":
            time_list = self.stop_entry.get().split(":")
            if len(time_list) == 1:
                self.time_to_stop = int(time_list[0])
            elif len(time_list) == 2:
                self.time_to_stop = int(time_list[0]) * 60 + int(time_list[1])
            elif len(time_list) == 3:
                self.time_to_stop = int(time_list[0]) * 60 * 60 + int(time_list[1]) * 60 + int(time_list[2])
            else:
                self.time_to_stop = 0
                
            if self.time_to_stop == 0:
                return
            self.stop_btn.config(text="cancel")
            self.stop_entry.configure(state="disabled")
            self.schedule_running = True
            self.stop_timer = threading.Timer(1, self._on_stop).start()
        else:
            self._reset_schedule()
                
    def _on_stop(self):
        if not self.schedule_running:
            return
        
        self.time_to_stop -= 1
        hour = self.time_to_stop // 3600
        min = self.time_to_stop % 3600 // 60
        seconds = self.time_to_stop % 3600 % 60

        self.stop_entry.configure(state="normal")
        self.stop_entry.delete(0, tk.END)
        self.stop_entry.insert(0, f'{hour}:{min}:{seconds}')        
        self.stop_entry.configure(state="disabled")
        
        if self.time_to_stop <= 0:
            self._reset_schedule()
            self._stop_game()
        else:
            self.stop_timer = threading.Timer(1, self._on_stop).start()
        
    def _reset_schedule(self):
        self.stop_btn.config(text="setup")
        self.stop_entry.configure(state="normal")
        self.schedule_running = False
        if self.stop_timer is not None:
            self.stop_timer.cancel()
            self.stop_timer = None

    def _stop_game(self):
        config.bot.stop_game()

class PetSettings(Configurable):
    DEFAULT_CONFIG = {
        'Auto-feed': False,
        'Num pets': 1
    }

    def get(self, key):
        return self.config[key]

    def set(self, key, value):
        assert key in self.config
        self.config[key] = value
