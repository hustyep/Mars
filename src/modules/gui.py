"""User friendly GUI to interact with Mars."""

import time
import threading
import tkinter as tk
from tkinter import ttk
from os.path import basename
from src.gui import Menu, View, Edit, Settings, Macros
from src.common import settings
from src.common.interfaces import Observer, Subject
from src.routine.layout import layout
from src.routine.routine import routine
from src.modules.bot import bot
from src.modules.listener import listener
from src.command_book.command_book import command_book

class GUI(Observer):
    DISPLAY_FRAME_RATE = 30
    RESOLUTIONS = {
        'DEFAULT': '800x800',
        'Edit': '1400x800'
    }

    def __init__(self):
        super().__init__()
        bot.attach(self)
        command_book.attach(self)
        routine.attach(self)
        listener.attach(self)
        
        self.root = tk.Tk()
        self.root.title('Mars')
        icon = tk.PhotoImage(file='assets/icon.png')
        self.root.iconphoto(False, icon)
        self.root.geometry(GUI.RESOLUTIONS['DEFAULT'])
        self.root.resizable(True, True)

        # Initialize GUI variables
        self.routine_var = tk.StringVar()

        # Build the GUI
        self.menu = Menu(self.root)
        self.root.config(menu=self.menu)

        self.navigation = ttk.Notebook(self.root)

        self.view = View(self.navigation, routine_var=self.routine_var)
        self.edit = Edit(self.navigation, routine_var=self.routine_var, curr_cb=self.view.status.curr_cb)
        self.settings = Settings(self.navigation)
        self.macro = Macros(self.navigation)

        self.navigation.pack(expand=True, fill='both')
        self.navigation.bind('<<NotebookTabChanged>>', self._resize_window)
        self.root.focus()

    def set_routine(self, arr):
        self.routine_var.set(arr)

    def clear_routine_info(self):
        """
        Clears information in various GUI elements regarding the current routine.
        Does not clear Listboxes containing routine Components, as that is handled by Routine.
        """

        self.view.details.clear_info()
        self.view.status.set_routine('')

        self.edit.minimap.redraw()
        self.edit.routine.commands.clear_contents()
        self.edit.routine.commands.update_display()
        self.edit.editor.reset()

    def _resize_window(self, e):
        """Callback to resize entire Tkinter window every time a new Page is selected."""

        nav = e.widget
        curr_id = nav.select()
        nav.nametowidget(curr_id).focus()      # Focus the current Tab
        page = nav.tab(curr_id, 'text')
        if self.root.state() != 'zoomed':
            if page in GUI.RESOLUTIONS:
                self.root.geometry(GUI.RESOLUTIONS[page])
            else:
                self.root.geometry(GUI.RESOLUTIONS['DEFAULT'])

    def start(self):
        """Starts the GUI as well as any scheduled functions."""

        display_thread = threading.Thread(target=self._display_minimap)
        display_thread.daemon = True
        display_thread.start()

        layout_thread = threading.Thread(target=self._save_layout)
        layout_thread.daemon = True
        layout_thread.start()

        self.root.mainloop()

    def _display_minimap(self):
        delay = 1 / GUI.DISPLAY_FRAME_RATE
        while True:
            self.view.minimap.display_minimap()
            time.sleep(delay)

    def _save_layout(self):
        """Periodically saves the current Layout object."""

        while True:
            if layout is not None and settings.record_layout:
                layout.save()
            time.sleep(5)
            
    def update(self, subject: Subject, *args, **kwargs) -> None:
        if subject == bot:
            type = args[0]
            if type == 'notify_level':
                self.settings.notification.notice_level.set(args[1])
                self.settings.notification.notification_settings.save_config()
            else:
                index = args[1]
                self.view.routine.select(index)
                self.view.details.display_info(index)
        elif subject == command_book:
            self.settings.update_class_bindings()
            self.menu.file.enable_routine_state()
            self.view.status.set_cb(command_book.name)
        elif subject == routine:
            match (args[0]):
                case 'clear':
                    self.clear_routine_info()
                case 'update':
                    self.set_routine(routine.display)
                    self.view.details.update_details()
                case 'load':
                    self.view.status.set_routine(basename(routine.path))
                    self.edit.minimap.draw_default()
        elif subject == listener:
            match (args[0]):
                case 'recalibrated':
                    self.edit.minimap.redraw()
                case 'record':
                    self.edit.record.add_entry(args[2], args[1])


if __name__ == '__main__':
    gui = GUI()
    gui.start()
