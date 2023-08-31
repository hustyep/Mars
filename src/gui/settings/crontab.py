import tkinter as tk
import threading
from src.gui.interfaces import LabelFrame, Frame
from src.common.action_simulator import ActionSimulator

class Crontab(LabelFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'Crontab', **kwargs)
        
        self.time_to_stop = 0
        self.time_to_start = 0
        
        self.stop_timer: threading.Timer = None
        self.start_schedule: threading.Timer = None
        self.schedule_running = False

        # 定时任务
        delay_row = Frame(self)
        delay_row.pack(side=tk.TOP, fill='x', expand=True, pady=(0, 5), padx=5)
        
        label = tk.Label(delay_row, text='Time to stop:')
        label.pack(side=tk.LEFT, padx=(0, 5), fill='x')
        
        display_var = tk.StringVar(value='60:00')
        self.stop_entry = tk.Entry(delay_row,
                         validate='key',
                         textvariable = display_var,
                         width=15,
                         takefocus=False)
        self.stop_entry.pack(side=tk.LEFT, padx=(15, 5))
        
        self.stop_btn = tk.Button(delay_row, text='setup', command=self._on_time_to_stop)
        self.stop_btn.pack(side=tk.RIGHT, padx=5, pady=5)
        
    
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
        ActionSimulator.stop_game()
