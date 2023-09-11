import os
import tkinter as tk
from src.common import config, utils
from src.gui.interfaces import MenuBarItem
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import askyesno
from src.common.interfaces import Configurable
import threading
from src.modules.bot import bot


class File(MenuBarItem):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 'File', **kwargs)
        # parent.add_cascade(label='File', menu=self)
        config.file_setting = File_Setting('files')

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

        load_command_menu = tk.Menu(self, tearoff=0)
        load_command_menu.add_command(label='Open File...',
                                      command=utils.async_callback(self, File._load_commands))
        load_command_menu.add_separator()
        # load_command_menu.add_command(label='night_load',
        #                                   command=lambda: File._load_command_by_name('night_lord'))
        # load_command_menu.add_command(label='shadower',
        #                                   command=lambda: File._load_command_by_name('shadower'))
        for file in get_command_books():
            load_command_menu.add_command(label=file,
                                          command=lambda name=file: File._load_command_by_name(name))
        self.add_cascade(label='Load Command Book',
                         menu=load_command_menu)

        self.load_routine_menu = tk.Menu(self, tearoff=0)
        self.load_routine_menu.add_command(label='Open File...',
                                           command=utils.async_callback(self, File._load_routine))
        self.load_routine_menu.add_separator()

        self.add_cascade(label='Load Routine',
                         menu=self.load_routine_menu,
                         state=tk.DISABLED)

        # self.add_command(
        #     label='Load Routine',
        #     command=utils.async_callback(self, File._load_routine),
        #     state=tk.DISABLED
        # )

        threading.Timer(1, self.loadDefault).start()

    def loadDefault(self):

        bot.load_commands(config.file_setting.get('command_book_path'))
        config.routine.load(config.file_setting.get("routine_path"))

    def enable_routine_state(self):
        self.entryconfig('New Routine', state=tk.NORMAL)
        self.entryconfig('Save Routine', state=tk.NORMAL)
        self.entryconfig('Load Routine', state=tk.NORMAL)

        self.load_routine_menu.delete(2, tk.END)
        
        command_path = config.file_setting.get('command_book_path')
        command_name = os.path.basename(command_path)[:-3]

        for file in get_routines(command_name):
            self.load_routine_menu.add_command(label=file,
                                               command=lambda name=file: File._load_routine_by_name(name))

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
        file_path = askopenfilename(initialdir=get_command_books_dir(),
                                    title='Select a command book',
                                    filetypes=[('*.py', '*.py')])
        File._load_command(file_path)

    @staticmethod
    @utils.run_if_disabled('\n[!] Cannot load command books while Mars is enabled')
    def _load_command(file_path):
        if file_path:
            config.file_setting.set('command_book_path', file_path)
            config.file_setting.save_config()
            bot.load_commands(file_path)

    def _load_command_by_name(name):
        target = os.path.join(config.RESOURCES_DIR,
                              'command_books', name + '.py')
        File._load_command(target)
        
    def _load_routine_by_name(name):
        command_path = config.file_setting.get('command_book_path')
        command_name = os.path.basename(command_path)[:-3]
        target = os.path.join(config.RESOURCES_DIR,
                              'routines', command_name, name + '.csv')
        config.file_setting.set('routine_path', target)
        config.file_setting.save_config()
        config.routine.load(target)


def get_command_books_dir() -> str:
    target = os.path.join(config.RESOURCES_DIR,
                          'command_books')
    if not os.path.exists(target):
        os.makedirs(target)
    return target


def get_command_books() -> list:
    books = []
    folder = get_command_books_dir()
    for root, ds, fs in os.walk(folder):
        for f in fs:
            if f.endswith(".py"):
                books.append(f[:-3])
    return books


def get_routines(command_name) -> list:
    routines = []
    folder = get_routines_dir(command_name)
    for root, ds, fs in os.walk(folder):
        for f in fs:
            if f.endswith(".csv"):
                routines.append(f[:-4])
    return routines


def get_routines_dir(command_name=None):
    if command_name is None:
        command_name = config.command_book.name
    target = os.path.join(config.RESOURCES_DIR,
                          'routines', command_name)
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
