import os
import tkinter as tk
from src.common import config, utils
from src.gui.interfaces import MenuBarItem
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import askyesno
from src.common.interfaces import Configurable
import threading

class File(MenuBarItem):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'File', **kwargs)
        # parent.add_cascade(label='File', menu=self)
        config.file_setting = File_Setting('files')

        threading.Timer(1, self.loadDefault).start()

        self.add_command(
            label='New Routine',
            command=utils.async_callback(self, File._new_routine),
            state=tk.DISABLED
        )
        self.add_command(
            label='Save Routine',
            command=utils.async_callback(self, File._save_routine),
            state=tk.DISABLED
        )
        self.add_separator()
        self.add_command(label='Load Command Book', command=utils.async_callback(self, File._load_commands))
        self.add_command(
            label='Load Routine',
            command=utils.async_callback(self, File._load_routine),
            state=tk.DISABLED
        )

    def loadDefault(self):

        config.bot.load_commands(config.file_setting.get('command_book_path'))
        config.routine.load(config.file_setting.get("routine_path"))

    def enable_routine_state(self):
        self.entryconfig('New Routine', state=tk.NORMAL)
        self.entryconfig('Save Routine', state=tk.NORMAL)
        self.entryconfig('Load Routine', state=tk.NORMAL)

    @staticmethod
    @utils.run_if_disabled('\n[!] Cannot create a new routine while Mars is enabled')
    def _new_routine():
        if config.routine.dirty:
            if not askyesno(title='New Routine',
                            message='The current routine has unsaved changes. '
                                    'Would you like to proceed anyways?',
                            icon='warning'):
                return
        config.routine.clear()

    @staticmethod
    @utils.run_if_disabled('\n[!] Cannot save routines while Mars is enabled')
    def _save_routine():
        file_path = asksaveasfilename(initialdir=get_routines_dir(),
                                      title='Save routine',
                                      filetypes=[('*.csv', '*.csv')],
                                      defaultextension='*.csv')
        if file_path:
            config.routine.save(file_path)

    @staticmethod
    @utils.run_if_disabled('\n[!] Cannot load routines while Mars is enabled')
    def _load_routine():
        if config.routine.dirty:
            if not askyesno(title='Load Routine',
                            message='The current routine has unsaved changes. '
                                    'Would you like to proceed anyways?',
                            icon='warning'):
                return
        file_path = askopenfilename(initialdir=get_routines_dir(),
                                    title='Select a routine',
                                    filetypes=[('*.csv', '*.csv')])
        if file_path:
            config.file_setting.set('routine_path', file_path)
            config.file_setting.save_config()
            config.routine.load(file_path)

    @staticmethod
    @utils.run_if_disabled('\n[!] Cannot load command books while Mars is enabled')
    def _load_commands():
        if config.routine.dirty:
            if not askyesno(title='Load Command Book',
                            message='Loading a new command book will discard the current routine, '
                                    'which has unsaved changes. Would you like to proceed anyways?',
                            icon='warning'):
                return
        file_path = askopenfilename(initialdir=os.path.join(config.RESOURCES_DIR, 'command_books'),
                                    title='Select a command book',
                                    filetypes=[('*.py', '*.py')])
        if file_path:
            config.file_setting.set('command_book_path', file_path)
            config.file_setting.save_config()
            config.bot.load_commands(file_path)


def get_routines_dir():
    target = os.path.join(config.RESOURCES_DIR, 'routines', config.bot.command_book.name)
    if not os.path.exists(target):
        os.makedirs(target)
    return target


class File_Setting(Configurable):
    DEFAULT_CONFIG = {
        'command_book_path': 'resources/command_books/shadower.py',
        'routine_path': 'resources/routines/shadower/ResarchTrain1.csv'
    }

    def get(self, key):
        return self.config[key]

    def set(self, key, value):
        assert key in self.config
        self.config[key] = value