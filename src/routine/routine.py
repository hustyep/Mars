"""A collection of classes used in the 'machine code' generated by Mars's compiler for each routine."""

import csv
import cv2
from os.path import splitext, basename

from src.common import settings, utils
from src.routine.components import Point, Label, Jump, Setting, SYMBOLS
from src.routine.commands import Command
from src.routine.layout import layout
from src.modules.gui import gui
from src.command_book.command_book import command_book

def update(func):
    """
    Decorator function that updates both the displayed routine and details
    for all mutative Routine operations.
    """

    def f(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        gui.set_routine(self.display)
        gui.view.details.update_details()
        return result
    return f


def dirty(func):
    """Decorator function that sets the dirty bit for mutative Routine operations."""

    def f(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.dirty = True
        return result
    return f


class Routine:
    """Describes a routine file in Mars's custom 'machine code'."""

    def __init__(self):
        self.dirty = False
        self.path = ''
        self.labels = {}
        self.index = 0
        self.sequence = []
        self.display = []       # Updated alongside sequence
        self.mob_template = []
        self.elite_template = []
        self.boss_template = []
        self.role_template = None
        self.guard_point_l = (100, 0)
        self.guard_point_r = (0, 0)

    @dirty
    @update
    def set(self, arr):
        self.sequence = arr
        self.display = [str(x) for x in arr]

    @dirty
    @update
    def append_component(self, p):
        self.sequence.append(p)
        self.display.append(str(p))

    @dirty
    @update
    def append_command(self, i, c):
        """Appends Command object C to the Point at index I in the sequence."""

        target = self.sequence[i]
        target.commands.append(c)

    @dirty
    @update
    def move_component_up(self, i):
        """Moves the component at index I upward if possible."""

        if i > 0:
            temp_s = self.sequence[i-1]
            temp_d = self.display[i-1]
            self.sequence[i-1] = self.sequence[i]
            self.display[i-1] = self.display[i]
            self.sequence[i] = temp_s
            self.display[i] = temp_d
            return i - 1
        return i

    @dirty
    @update
    def move_component_down(self, i):
        if i < len(self.sequence) - 1:
            temp_s = self.sequence[i+1]
            temp_d = self.display[i+1]
            self.sequence[i+1] = self.sequence[i]
            self.display[i+1] = self.display[i]
            self.sequence[i] = temp_s
            self.display[i] = temp_d
            return i + 1
        return i

    @dirty
    @update
    def move_command_up(self, i, j):
        """
        Within the Point at routine index I, moves the Command at index J upward
        if possible and updates the Edit UI.
        """

        point = self.sequence[i]
        if j > 0:
            temp = point.commands[j-1]
            point.commands[j-1] = point.commands[j]
            point.commands[j] = temp
            return j - 1
        return j

    @dirty
    @update
    def move_command_down(self, i, j):
        point = self.sequence[i]
        if j < len(point.commands) - 1:
            temp = point.commands[j+1]
            point.commands[j+1] = point.commands[j]
            point.commands[j] = temp
            return j + 1
        return j

    @dirty
    @update
    def delete_component(self, i):
        """Deletes the Component at index I."""

        self.sequence.pop(i)
        self.display.pop(i)

    @dirty
    @update
    def delete_command(self, i, j):
        """Within the Point at routine index I, deletes the Command at index J."""

        point = self.sequence[i]
        point.commands.pop(j)

    @update
    def update_component(self, i, new_kwargs):
        target = self.sequence[i]
        try:
            target.update(**new_kwargs)
            self.display[i] = str(target)
            self.dirty = True
        except (ValueError, TypeError) as e:
            print(f"\n[!] Found invalid arguments for '{target.__class__.__name__}':")
            print(f"{' ' * 4} -  {e}")

    @update
    def update_command(self, i, j, new_kwargs):
        target = self.sequence[i].commands[j]
        try:
            target.update(**new_kwargs)
            self.display[i] = str(self.sequence[i])
            self.dirty = True
        except (ValueError, TypeError) as e:
            print(f"\n[!] Found invalid arguments for '{target.__class__.__name__}':")
            print(f"{' ' * 4} -  {e}")

    @utils.run_if_enabled
    def step(self):
        """Increments config.seq_index and wraps back to 0 at the end of config.sequence."""

        self.index = (self.index + 1) % len(self.sequence)

    def save(self, file_path=None):
        """Encodes and saves the current Routine at location PATH."""
        if not file_path:
            file_path = self.path

        result = []
        for item in self.sequence:
            result.append(item.encode())
            if isinstance(item, Point):
                for c in item.commands:
                    result.append(' ' * 4 + c.encode())
        result.append('')

        with open(file_path, 'w') as file:
            file.write('\n'.join(result))
        self.dirty = False

        utils.print_separator()
        print(f"[~] Saved routine to '{basename(file_path)}'.")

    def clear(self):
        self.index = 0
        self.set([])
        self.dirty = False
        self.path = ''
        self.mob_template = []
        self.elite_template = []
        self.boss_template = []
        self.role_template = None
        self.guard_point_l = (100, 0)
        self.guard_point_r = (0, 0)
        layout.clear()
        settings.reset()

        gui.clear_routine_info()

    def load(self, file=None):
        """
        Attempts to load FILE into a sequence of Components. If no file path is provided, attempts to
        load the previous routine file.
        :param file:    The file's path.
        :return:        None
        """

        utils.print_separator()
        print(f"[~] Loading routine '{basename(file)}':")

        if not file:
            if self.path:
                file = self.path
                print(' *  File path not provided, using previously loaded routine')
            else:
                print('[!] File path not provided, no routine was previously loaded either')
                return False

        ext = splitext(file)[1]
        if ext != '.csv':
            print(f" !  '{ext}' is not a supported file extension.")
            return False

        self.clear()

        # Compile and Link
        self.compile(file)
        for c in self.sequence:
            if isinstance(c, Jump):
                c.bind()

        self.setup_template()

        self.dirty = False
        self.path = file
        layout.load(file)
        gui.view.status.set_routine(basename(file))
        gui.edit.minimap.draw_default()
        print(f" ~  Finished loading routine '{basename(splitext(file)[0])}'.")

    def compile(self, file):
        self.labels = {}
        with open(file, newline='') as f:
            csv_reader = csv.reader(f, skipinitialspace=True)
            curr_point = None
            line = 1
            for row in csv_reader:
                result = self._eval(row, line)
                if result:
                    if isinstance(result, Command):
                        if curr_point:
                            curr_point.commands.append(result)
                    else:
                        self.append_component(result)
                        if isinstance(result, Point):
                            curr_point = result
                            if curr_point.location[0] < self.guard_point_l[0]:
                                self.guard_point_l = curr_point.location
                            elif curr_point.location[0] > self.guard_point_r[0]:
                                self.guard_point_r = curr_point.location
                        elif isinstance(result, Setting):
                            result.main()
                line += 1

    def _eval(self, row, i):
        if row and isinstance(row, list):
            first, rest = row[0].lower(), row[1:]
            args, kwargs = utils.separate_args(rest)
            line_error = f' !  Line {i}: '

            if first in SYMBOLS:
                c = SYMBOLS[first]
            elif first in command_book:
                c = command_book[first]
            else:
                print(line_error + f"Command '{first}' does not exist.")
                return

            try:
                obj = c(*args, **kwargs)
                if isinstance(obj, Label):
                    obj.set_index(len(self))
                    self.labels[obj.label] = obj
                return obj
            except (ValueError, TypeError) as e:
                print(line_error + f"Found invalid arguments for '{c.__name__}':")
                print(f"{' ' * 4} -  {e}")

    def setup_template(self):
        if len(settings.mob_name) > 0:
            try:
                mob_template = cv2.imread(f'assets/mobs/{settings.mob_name}.png', 0)
                elite_template = cv2.imread(f'assets/mobs/{settings.mob_name}_elite.png', 0)
                boss_template = cv2.imread(f'assets/mobs/{settings.mob_name}_boss.png', 0)
            except:
                pass
            if mob_template is not None:
                self.mob_template.append(mob_template)
                self.mob_template.append(cv2.flip(mob_template, 1))
            
            if elite_template is not None:
                self.elite_template.append(elite_template)
                self.elite_template.append(cv2.flip(elite_template, 1))
            elif mob_template:
                elite_template = cv2.resize(mob_template, None, fx=2, fy=2)
                self.elite_template.append(elite_template)
                self.elite_template.append(cv2.flip(elite_template, 1))   
                             
            if boss_template is not None:
                self.boss_template.append(boss_template)
                self.boss_template.append(cv2.flip(boss_template, 1))
        
        if len(settings.role_name) > 0:
            try:
                self.role_template = cv2.imread(f'assets/roles/player_{settings.role_name}_template.png', 0)
            except:
                pass
                
    @staticmethod
    def get_all_components():
        """Returns a dictionary mapping all creatable Components to their names."""

        options = command_book.dict.copy()
        for e in (Point, Label, Jump, Setting):
            options[e.__name__.lower()] = e
        return options

    def __getitem__(self, i):
        return self.sequence[i]

    def __len__(self):
        return len(self.sequence)
    

routine = Routine()
