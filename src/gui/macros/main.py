"""Displays Mars's current settings and allows the user to edit them."""

import tkinter as tk
from src.gui.macros.misc import Misc
from src.gui.macros.shadower import Shadower
from src.gui.interfaces import Tab

class Macros(Tab):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'Macros', **kwargs)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(3, weight=1)

        self.misc = Misc(self)
        self.misc.grid(row=0, column=2, sticky=tk.NSEW, padx=10, pady=10)
        
        self.shadower = Shadower(self)
        self.shadower.grid(row=1, column=2, sticky=tk.NSEW, padx=10, pady=10)