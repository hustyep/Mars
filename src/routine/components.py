"""A collection of classes used to execute a Routine."""

import time
from src.common import config, utils, settings

#################################
#       Routine Components      #
#################################


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


class Point(Component):
    """Represents a location in a user-defined routine."""

    id = '*'

    def __init__(self, x, y, frequency=1, interval=0, skip='False', adjust='False'):
        super().__init__(locals())
        self.x = int(x)
        self.y = int(y)
        self.location = (self.x, self.y)
        self.frequency = settings.validate_nonnegative_int(frequency)
        self.interval = settings.validate_nonnegative_float(interval)
        if self.interval > 0:
            self.counter = (
                time.time() + 14) if settings.validate_boolean(skip) else 0
        else:
            self.counter = int(settings.validate_boolean(skip))
        self.adjust = settings.validate_boolean(adjust)
        if not hasattr(self, 'commands'):       # Updating Point should not clear commands
            self.commands = []

    def main(self):
        """Executes the set of actions associated with this Point."""
        # self.print_debug_info()

        if self.interval > 0:
            if self.counter == 0 or time.time() - self.counter >= self.interval:
                self._main()
                self.counter = time.time()
        else:
            if self.counter == 0:
                self._main()
            self._increment_counter()
            
            
    def _main(self):
        for command in self.commands:
            command.execute()
            
    @utils.run_if_enabled
    def _increment_counter(self):
        """Increments this Point's counter, wrapping back to 0 at the upper bound."""

        self.counter = (self.counter + 1) % self.frequency

    def info(self):
        curr = super().info()
        curr['vars'].pop('location', None)
        curr['vars']['commands'] = ', '.join([c.id for c in self.commands])
        return curr

    def __str__(self):
        return f'  * {self.location}'


class Label(Component):
    id = '@'

    def __init__(self, label):
        super().__init__(locals())
        self.label = str(label)
        # if self.label in routine.labels:
        #     raise ValueError
        self.links = set()
        self.index = None

    def set_index(self, i):
        self.index = i

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


SYMBOLS = {
    '*': Point,
    '@': Label,
    '>': Jump,
    '$': Setting
}