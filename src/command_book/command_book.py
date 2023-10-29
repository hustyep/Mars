import os
import inspect
import importlib
import traceback
from os.path import basename, splitext
from src.common import config, utils
from src.common.interfaces import Configurable, Subject
from src.routine import commands

CB_KEYBINDING_DIR = os.path.join('resources', 'keybindings')


class CommandBook(Configurable, Subject):
    def __init__(self):
        self.name = ''
        self.buff = commands.Buff()
        self.potion = commands.Potion()
        self.move = commands.Move
        self.adjust = commands.Adjust
        self.adjustx = commands.AdjustX
        
        self.DEFAULT_CONFIG = {}
        self.dict = None
        self.module = None
        
        self._observers = []
        super().__init__(self.name, directory=CB_KEYBINDING_DIR)
        
    def load_commands(self, file):
        self.name = splitext(basename(file))[0]
        config.class_name = self.name
        result = self._load_commands(file)
        if result is None:
            raise ValueError(f"Invalid command book at '{file}'")
        self.dict, self.module = result
        self.TARGET = self.name
        self.config = self.DEFAULT_CONFIG.copy()
        self.load_config()
        self.notify()
        
    def _load_commands(self, file):
        """Prompts the user to select a command module to import. Updates config's command book."""

        utils.print_separator()
        print(f"[~] Loading command book '{basename(file)}':")

        ext = splitext(file)[1]
        if ext != '.py':
            print(f" !  '{ext}' is not a supported file extension.")
            return

        new_step = commands.step
        new_cb = {}
        for c in (commands.Wait, commands.Walk, commands.Fall):
            new_cb[c.__name__.lower()] = c

        # Import the desired command book file
        target = '.'.join(['resources', 'command_books', self.name])
        try:
            module = importlib.import_module(target)
            module = importlib.reload(module)
        except ImportError:     # Display errors in the target Command Book
            print(' !  Errors during compilation:\n')
            for line in traceback.format_exc().split('\n'):
                line = line.rstrip()
                if line:
                    print(' ' * 4 + line)
            print(f"\n !  Command book '{self.name}' was not loaded")
            return

        # Load key map
        if hasattr(module, 'Keybindings'):
            default_config = {}
            for key, value in module.Keybindings.__dict__.items():
                if not key.startswith('__') and not key.endswith('__'):
                    default_config[key] = value
            self.DEFAULT_CONFIG = default_config
        else:
            print(f" !  Error loading command book '{self.name}', keymap class 'Keybindings' is missing")
            return

        # Check if the 'step' function has been implemented
        step_found = False
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.lower() == 'step':
                step_found = True
                new_step = func

        # Populate the new command book
        for name, command in inspect.getmembers(module, inspect.isclass):
            if issubclass(command, commands.Command):
                new_cb[name.lower()] = command

        # Check if required commands have been implemented and overridden
        required_found = True
        for command in (commands.Buff, commands.Potion, commands.MoveUp, commands.MoveDown):
            name = command.__name__.lower()
            if name not in new_cb:
                required_found = False
                new_cb[name] = command
                print(f" !  Error: Must implement required command '{name}'.")

        # Look for overridden movement commands
        movement_found = True
        for command in (commands.Move, commands.Adjust, commands.AdjustX):
            name = command.__name__.lower()
            if name not in new_cb:
                movement_found = False
                new_cb[name] = command

        if not step_found and not movement_found:
            print(f" !  Error: Must either implement both 'Move' and 'Adjust' commands, "
                  f"or the function 'step'")
        if required_found and (step_found or movement_found):
            self.buff = new_cb['buff']()
            self.potion = new_cb["potion"]()
            self.move = new_cb["move"]
            self.adjust = new_cb["adjust"]
            self.adjustx = new_cb["adjustx"]
            commands.step = new_step
            commands.MoveUp = new_cb['moveup']
            commands.MoveDown = new_cb['movedown']
            # routine.clear()
            print(f" ~  Successfully loaded command book '{self.name}'")
            return new_cb, module
        else:
            print(f" !  Command book '{self.name}' was not loaded")

    def __getitem__(self, item):
        return self.dict[item]

    def __contains__(self, item):
        return item in self.dict

    def load_config(self):
        super().load_config()
        self._set_keybinds()

    def save_config(self):
        self._set_keybinds()
        super().save_config()

    def _set_keybinds(self):
        for k, v in self.config.items():
            setattr(self.module.Keybindings, k, v)


command_book = CommandBook()