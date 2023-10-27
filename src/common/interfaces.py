from __future__ import annotations
import os
import pickle
from abc import ABC, abstractmethod
from typing import List
from src.common import config, utils

class Observer(ABC):
    """
    The Observer interface declares the update method, used by subjects.
    """

    @abstractmethod
    def update(self, subject: Subject, *args, **kwargs) -> None:
        """
        Receive update from subject.
        """
        pass


class Subject():
    """
    The Subject interface declares a set of methods for managing subscribers.
    """

    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        """
        Attach an observer to the subject.
        """
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """
        Detach an observer from the subject.
        """
        self._observers.remove(observer)

    def notify(self, *args, **kwargs) -> None:
        """
        Subject: Notifying observers...
        """
        for observer in self._observers:
            observer.update(self, *args, **kwargs)

class Configurable:
    TARGET = 'default_configurable'
    DIRECTORY = '.settings'
    DEFAULT_CONFIG = {          # Must be overridden by subclass
        'Default configuration': 'None'
    }

    def __init__(self, target, directory='.settings'):
        assert self.DEFAULT_CONFIG != Configurable.DEFAULT_CONFIG, 'Must override Configurable.DEFAULT_CONFIG'
        self.TARGET = target
        self.DIRECTORY = directory
        self.config = self.DEFAULT_CONFIG.copy()        # Shallow copy, should only contain primitives
        self.load_config()

    def load_config(self):
        path = os.path.join(self.DIRECTORY, self.TARGET)
        if os.path.isfile(path):
            with open(path, 'rb') as file:
                loaded = pickle.load(file)
                self.config = {key: loaded.get(key, '') for key in self.DEFAULT_CONFIG}
        else:
            self.save_config()

    def save_config(self):
        if not self.TARGET:
            return
        path = os.path.join(self.DIRECTORY, self.TARGET)
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(path, 'wb') as file:
            pickle.dump(self.config, file)

class Component:
    id = 'Routine Component'
    PRIMITIVES = {int, str, bool, float}

    def __init__(self, *args, **kwargs):
        if len(args) > 1:
            raise TypeError(
                'Component superclass __init__ only accepts 1 (optional) argument: LOCALS')
        if len(kwargs) != 0:
            raise TypeError(
                'Component superclass __init__ does not accept any keyword arguments')
        if len(args) == 0:
            self.kwargs = {}
        elif type(args[0]) != dict:
            raise TypeError(
                "Component superclass __init__ only accepts arguments of type 'dict'.")
        else:
            self.kwargs = args[0].copy()
            self.kwargs.pop('__class__')
            self.kwargs.pop('self')

    @utils.run_if_enabled
    def execute(self):
        self.main()

    def main(self):
        self.print_debug_info()

    def update(self, *args, **kwargs):
        """Updates this Component's constructor arguments with new arguments."""

        # Validate arguments before actually updating values
        self.__class__(*args, **kwargs)
        self.__init__(*args, **kwargs)

    def info(self):
        """Returns a dictionary of useful information about this Component."""

        return {
            'name': self.__class__.__name__,
            'vars': self.kwargs.copy()
        }

    def encode(self):
        """Encodes an object using its ID and its __init__ arguments."""

        arr = [self.id]
        for key, value in self.kwargs.items():
            if key != 'id' and type(self.kwargs[key]) in Component.PRIMITIVES:
                arr.append(f'{key}={value}')
        return ', '.join(arr)
    
    def print_debug_info(self):
        if config.notice_level == 5:
            print(self.info())