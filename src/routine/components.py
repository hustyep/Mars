"""A collection of classes used to execute a Routine."""

import time
from src.routine.commands import Command, Move
from src.common.interfaces import Component
from src.common import utils, settings

#################################
#       Routine Components      #
#################################


class Point(Component):
    """Represents a location in a user-defined routine."""

    id = '*'

    def __init__(self, x, y, interval=0, tolerance=0, skip='False') -> None:
        super().__init__(locals())
        self.x = int(x)
        self.y = int(y)
        self.location = (self.x, self.y)
        self.interval = settings.validate_nonnegative_int(interval)
        self.tolerance = settings.move_tolerance if int(tolerance) == 0 else int(tolerance)
        self.skip = settings.validate_boolean(skip)
        self.last_execute_time = 0
        if not hasattr(self, 'commands'):       # Updating Point should not clear commands
            self.commands: list[Command] = []

    def main(self):
        """Executes the set of actions associated with this Point."""
        # self.print_debug_info()

        if self.interval > 0:
            now = time.time()
            if self.skip and self.last_execute_time == 0:
                self.last_execute_time = now
            if now - self.last_execute_time >= self.interval:
                self._main()
        else:
            self._main()
            
    def _main(self):
        self.last_execute_time = time.time()
        Move(*self.location).execute()
        for command in self.commands:
            command.execute()

    def info(self):
        curr = super().info()
        curr['vars'].pop('location', None)
        curr['vars']['commands'] = ', '.join([c.id for c in self.commands])
        return curr

    def __str__(self):
        return f'  * {self.location}'


class Label(Component):
    id = '@'

    def __init__(self, label, interval, skip=False):
        super().__init__(locals())
        self.label = str(label)
        self.interval = settings.validate_nonnegative_int(interval)
        self.skip = settings.validate_boolean(skip)

        self.last_execute_time = 0
        self.components: list[Component] = []
        self.index = None

    def main(self):
        """Executes the series of actions associated with this Label."""
        # self.print_debug_info()

        if self.interval > 0:
            if time.time() - self.last_execute_time >= self.interval:
                self._main()
        else:
            self._main()
            
    def _main(self):
        for component in self.series:
            component.execute()

    def set_index(self, i):
        self.index = i

    def add_component(self, component: Component):
        self.components.append(component)

    def encode(self):
        return '\n' + super().encode()

    def info(self):
        curr = super().info()
        curr['vars']['index'] = self.index
        return curr

    def __delete__(self, instance):
        del self.links
        # routine.labels.pop(self.label)

    def __str__(self):
        return f'{self.label}:'


class Sequence(Component):
    """A series of actions."""
    
    id = '~'
    
    def __init__(self, label, interval, skip=False):
        super().__init__(locals())
        self.label = str(label)
        self.interval = settings.validate_nonnegative_int(interval)
        self.skip = settings.validate_boolean(skip)

        # if self.label in routine.labels:
        #     raise ValueError
        self.last_execute_time = time.time() + self.interval if skip else 0
        self.path: list[Point] = []
        self.index = None

    def main(self):
        """Executes the series of actions associated with this Sequence."""
        # self.print_debug_info()

        if self.interval > 0:
            if time.time() - self.last_execute_time >= self.interval:
                self._main()
        else:
            self._main()
            
    def _main(self):
        for point in self.series:
            point.execute()

    def add_component(self, component: Point):
        self.path.append(component)

    def set_index(self, i):
        self.index = i

    def encode(self):
        return '\n' + super().encode()

    def info(self):
        curr = super().info()
        curr['vars']['index'] = self.index
        curr['vars']['series'] = self.series
        return curr

    def __delete__(self, instance):
        del self.series
        # routine.labels.pop(self.label)

    def __str__(self):
        return f'{self.label}:'

class Jump(Component):
    """Jumps to the given Label."""

    id = '>'

    def __init__(self, label, frequency=1, skip='False'):
        super().__init__(locals())
        self.label = str(label)
        self.frequency = settings.validate_nonnegative_int(frequency)
        self.counter = int(settings.validate_boolean(skip))
        self.link = None

    def main(self):
        if self.link is None:
            print(f"\n[!] Label '{self.label}' does not exist.")
        else:
            # if self.counter == 0:
            #     routine.index = self.link.index
            self._increment_counter()

    @utils.run_if_enabled
    def _increment_counter(self):
        self.counter = (self.counter + 1) % self.frequency

    def bind(self):
        """
        Binds this Goto to its corresponding Label. If the Label's index changes, this Goto
        instance will automatically be able to access the updated value.
        :return:    Whether the binding was successful
        """

        # if self.label in routine.labels:
        #     self.link = routine.labels[self.label]
        #     self.link.links.add(self)
        #     return True
        return False

    def __delete__(self, instance):
        if self.link is not None:
            self.link.links.remove(self)

    def __str__(self):
        return f'  > {self.label}'


class Setting(Component):
    """Changes the value of the given setting variable."""

    id = '$'

    def __init__(self, target, value):
        super().__init__(locals())
        self.key = str(target)
        if self.key not in settings.SETTING_VALIDATORS:
            raise ValueError(f"Setting '{target}' does not exist")
        self.value = settings.SETTING_VALIDATORS[self.key](value)

    def main(self):
        setattr(settings, self.key, self.value)

    def __str__(self):
        return f'  $ {self.key} = {self.value}'


class End(Component):
    id = '#'
    
SYMBOLS = {
    '*': Point,
    '@': Label,
    '>': Jump,
    '$': Setting,
    '~': Sequence,
    '#': End,
}