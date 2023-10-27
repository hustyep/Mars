"""Displays Mars's current settings and allows the user to edit them."""

import tkinter as tk
from src.gui.interfaces import KeyBindings
from src.gui.settings.pets import Pets
from src.gui.settings.crontab import Crontab
from src.gui.settings.buffs import Buffs
from src.gui.settings.auto import Auto
from src.gui.settings.notification import Notification
from src.gui.interfaces import Tab, Frame
from src.modules.listener import listener
from src.command_book.command_book import command_book
from src.common import config

class Settings(Tab):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'Settings', **kwargs)
        config.gui_settings = self

        self.columnconfigure(0, weight=1)
        self.columnconfigure(3, weight=1)

        self.column1 = Frame(self)
        self.column1.grid(row=0, column=1, sticky=tk.N, padx=10, pady=10)

        self.auto = Auto(self.column1)
        self.auto.pack(side=tk.TOP, fill='x', expand=True, pady=(10, 0))
        self.notification = Notification(self.column1)
        self.notification.pack(side=tk.TOP, fill='x', expand=True, pady=(10, 0))
        self.crontab = Crontab(self.column1)
        self.crontab.pack(side=tk.TOP, fill='x', expand=True, pady=(10, 0))
        self.buffs = Buffs(self.column1)
        self.buffs.pack(side=tk.TOP, fill='x', expand=True, pady=(10, 0))
        self.pets = Pets(self.column1)
        self.pets.pack(side=tk.TOP, fill='x', expand=True, pady=(10, 0))

        self.column2 = Frame(self)
        self.column2.grid(row=0, column=2, sticky=tk.N, padx=10, pady=10)
        self.controls = KeyBindings(self.column2, 'Mars Controls', listener)
        self.controls.pack(side=tk.TOP, fill='x', expand=True)
        self.class_bindings = KeyBindings(self.column2, f'No Command Book Selected', None)
        self.class_bindings.pack(side=tk.TOP, fill='x', expand=True, pady=(10, 0))
        # self.common_bindings = KeyBindings(self.column2, 'In-game Keybindings', bot)
        # self.common_bindings.pack(side=tk.TOP, fill='x', expand=True, pady=(10, 0))
        
    def update_class_bindings(self):
        self.class_bindings.destroy()
        class_name = command_book.name.capitalize()
        self.class_bindings = KeyBindings(self.column2, f'{class_name} Keybindings', command_book)
        self.class_bindings.pack(side=tk.TOP, fill='x', expand=True)
