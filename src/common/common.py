from __future__ import annotations
from abc import ABC, abstractmethod
from random import randrange
from typing import List

def singleton(cls):
    _instance = {}

    def inner():
        if cls not in _instance:
            _instance[cls] = cls()
        return _instance[cls]
    return inner


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