"""
Namespace object for storing multi-level data.
Data can added on initialisation as a dictionary, a path to a directory and/or a path to a yaml_file
"""

import yaml
import copy
import re


from deeplodocus.utils.notification import Notification
from deeplodocus.utils.flags.notif import *
from deeplodocus.utils.flags.msg import *


class Namespace(object):

    def __init__(self, *args):
        """
        Author: SW
        Initialise the namespace by loading any given yaml files or dictionaries
        :param args: str or dict: yaml path or dictionary to be included in the namespace
        """
        for arg in args:
            if isinstance(arg, str):
                self.load(arg)
            elif isinstance(arg, dict):
                self.add(arg)
            else:
                print("Warning: unused argument %s" % arg)

    def add(self, dictionary, sub_space=None):
        """
        Author: SW
        Add a given dictionary into self.
        E.g. add(baz, ["foo", "bar"]), will load the contents of baz into self.foo.bar
        :param dictionary: dict: dictionary to add
        :param sub_space: str: a sub-space to load into
        :return: None
        """
        for key, item in self.__dict2namespace(dictionary).get().items():
            self.__add({key: item}, sub_space)

    def load(self, yaml_path, sub_space=None):
        """
        Author: SW
        Load a given yaml file into self.
        E.g. load("baz.yaml", sub_space=["foo", "bar"]) will load foo into self.foo.bar
        :param yaml_path: str: path to the yaml file.
        :param sub_space: str: a sub-space to load the yaml into.
        :return: None
        """
        for key, item in self.__yaml2namespace(yaml_path).get().items():
            self.__add({key: item}, sub_space)

    def copy(self):
        """
        Author: SW
        :return: Namespace: a deep copy of itself
        """
        return copy.deepcopy(self)

    def get(self, key=None):
        """
        Get data from the Namespace as a dictionary given a key or list of keys.
        Note: key can be a list of sub Namespace names for which get() will be called recursively.
        :param key: str or list of str: key of the sub item to be returned.
        :return: dict: data retrieved from the Namespace.
        """
        if key is None:
            return self.__dict__
        else:
            if isinstance(key, list):
                key = key[0] if len(key) == 1 else key
            if isinstance(key, list):
                return self.__dict__[key[0]].get(key[1:])
            elif isinstance(self.__dict__[key], Namespace):
                return self.__dict__[key].get()
            else:
                if isinstance(key, list):
                    return [self.__dict__[k] for k in key]
                else:
                    return self.__dict__[key]

    def save(self, file_path, tab_size=2):
        """
        Author: SW
        Save this Namespace as a yaml file.
        :param file_path: str: path to write yaml file to.
        :param tab_size: int: number of spaces to use per tab.
        :return: None
        """
        with open(file_path, "w") as file:
            file.write(self.__get_summary(tab_size=tab_size).replace(" None", " Null"))

    def summary(self, tab_size=2):
        """
        Author: SW
        Prints a summary of the Namespace contents using Notification.
        :param tab_size: int: number of spaces to user per tab.
        :return: None
        """
        summary = self.__get_summary(tab_size=tab_size).split("\n")
        summary = [line for line in summary if line]
        for line in summary:
            Notification(DEEP_NOTIF_INFO, line)

    def check(self, key, sub_space=None):
        """
        Author: SW
        Check the existence of of a given key.
        If the key is in a sub-namespace, a list of subsequent sub-spaces may be given.
        E.g. check("baz", ["foo", "bar"]), will check the existence of self.foo.bar.baz
        :param key: str: a key to check the existence of.
        :param sub_space: str: a subspace where the item is expected to be found.
        :return: bool: whether or not the subspace exists in namespace.
        """
        if key in self.get(sub_space).keys():
            return True
        elif sub_space is not None:
            sub_space = [sub_space] if not isinstance(sub_space, list) else sub_space
            item_path = DEEP_CONFIG_DIVIDER.join(sub_space + [key])
            Notification(DEEP_NOTIF_WARNING, DEEP_MSG_CONFIG_NOT_FOUND % item_path)
            return False
        else:
            return False

    def __get_summary(self, tab_size=2, tabs=0, line=None):
        """
        Author: SW
        Returns a summary of this namespace as a string.
        :param tab_size: int: number of spaces per tab.
        :param tabs: int: number of tabs to use (for internal use).
        :param line: str: the summary statement from a previous call (for internal use).
        :return: None
        """
        if line is None:
            line = ""
        for key, value in self.__dict__.items():
            if isinstance(value, Namespace):
                line += "%s%s:\n" % (" " * tab_size * tabs, key)
                line += value.__get_summary(tabs=tabs + 1)
            else:
                if isinstance(value, list):
                    line += "%s%s:\n" % (" " * tab_size * tabs, key)
                    for item in value:
                        if isinstance(item, str):
                            item = '"%s"' % item
                        line += "%s- %s\n" % (" " * (tab_size + 1) * tabs, item)
                else:
                    if isinstance(value, str):
                        value = '"%s"' % value
                    line += "%s%s: %s\n" % (" " * tab_size * tabs, key, value)
        return line

    def __dict2namespace(self, dictionary):
        """
        Given a dictionary, converts it into a Namespace object.
        :param dictionary: dict: a dictionary containing information to store as a Namespace.
        :return: Namespace containing all data from the dictionary.
        Note: the function is recursive and sub-dictionaries are represented as sub-Namespaces.
        """
        namespace = Namespace()
        for key, item in dictionary.items():
            if isinstance(item, dict):
                item = self.__dict2namespace(item)
            namespace.__add({key: item})
        return namespace

    def __yaml2namespace(self, file_name):
        """
        Given a yaml file, opens it and converts it to a Namespace object.
        :param file_name: str: path to a yaml file.
        :return: Namespace containing all data from the yaml file.
        """
        with open(file_name, "r") as file:
            dictionary = yaml.load(file)
            return self.__dict2namespace(dictionary)

    def __add(self, dictionary, sub_space=None):
        """
        Author: SW
        Add a new dictionary to the namespace.
        :param dictionary: dict: the dictionary of data to add.
        :param sub_space: str or list of str: path to a sub-space within the Namespace.
        :return: None.
        """
        if sub_space is None:
            self.__dict__.update(dictionary)
        else:
            if isinstance(sub_space, list):
                sub_space = sub_space[0] if len(sub_space) == 1 else sub_space
            if isinstance(sub_space, list):
                if sub_space[0] not in self.get().keys():
                    self.__dict__.update({sub_space[0]: Namespace()})
                try:
                    self.get()[sub_space[0]].__add(dictionary, sub_space[1:])
                except AttributeError:
                    raise AttributeError("Unable to add data to '%s', location not a namespace " % sub_space[0])
            else:
                if sub_space not in self.get().keys():
                    self.__dict__.update({sub_space: Namespace()})
                self.get()[sub_space].__add(dictionary)



# this is to convert the string written as a tuple into a python tuple
def yml_tuple_constructor(loader, node):
    # this little parse is really just for what I needed, feel free to change it!
    def parse_tup_el(el):
        # try to convert into int or float else keep the string
        if el.isdigit():
            return int(el)
        try:
            return float(el)
        except ValueError:
            return el

    value = loader.construct_scalar(node)
    # remove the ( ) from the string
    tup_elements = value[1:-1].split(',')
    # remove the last element if the tuple was written as (x,b,)
    if tup_elements[-1] == '':
        tup_elements.pop(-1)
    tup = tuple(map(parse_tup_el, tup_elements))
    return tup

# Add tuples to PyYaml
yaml.add_constructor(u'!tuple', yml_tuple_constructor)
# this is to spot the strings written as tuple in the yaml
yaml.add_implicit_resolver(u'!tuple', re.compile(r"\(([^,\W]{,},){,}[^,\W]*\)"))


if __name__ == "__main__":
    namespace = Namespace({"a": 1, "b": 2, "c": {"d": 5, "e": 6}})
    a = {"project": "../yaml1", "network": {"gv": 56, "you": 90}, "test" : (1, "a", 1.2)}
    namespace.add(a, ["c", "main", "moop"])
    namespace.summary()

