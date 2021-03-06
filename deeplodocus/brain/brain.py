import os
import time
import __main__

from deeplodocus import __version__
from deeplodocus.brain.frontal_lobe import FrontalLobe
from deeplodocus.utils.notification import Notification, DeepError
from deeplodocus.utils.flags import *
from deeplodocus.utils.namespace import Namespace
from deeplodocus.utils.logo import Logo
from deeplodocus.utils.end import End
from deeplodocus.utils.logs import Logs
from deeplodocus.brain.visual_cortex import VisualCortex
from deeplodocus.brain.thalamus import Thalamus


class Brain(FrontalLobe):
    """
    AUTHORS:
    --------

    :author: Alix Leroy
    :author: Samuel Westlake

    DESCRIPTION:
    ------------

    A Brain class that manages the commands of the user and allows to start the training
    PUBLIC METHODS:
    ---------------
    :method wake:
    :method sleep:
    :method save_config: Save all configuration files into self.config_dir.
    :method clear_config: Reset self.config to an empty Namespace.
    :method store_config: Store a copy of self.config in self._config.
    :method restore_config: Set self.config to a copy of self._config.
    :method load_config: Load self.config from self.config_dir.
    :method check_config: Check self.config for missing parameters and set data types accordingly.
    :method clear_logs: Deletes logs that are not to be kept, as decided in the config settings.
    :method close_logs: Closes logs that are to be kept and deletes logs that are to be deleted, see config settings.
    :method ui:

    PRIVATE METHODS:
    ----------------
    :method __init__:
    :method __check_config:
    :method __convert_dtype:
    :method __convert:
    :method __on_wake:
    :method __execute_command:
    :method __preprocess_command:
    :method __illegal_command_messages:
    :method __get_command_flags:
    """

    def __init__(self, config_dir):
        """
        AUTHORS:
        --------

        :author: Alix Leroy

        DESCRIPTION:
        ------------

        Initialize a Deeplodocus Brain

        PARAMETERS:
        -----------

        :param config_path->str: The config path

        RETURN:
        -------

        :return: None
        """
        FrontalLobe.__init__(self)  # Model Manager
        self.close_logs(force=True)
        self.config_dir = config_dir
        self.config_is_complete = False
        Logo(version=__version__)
        self.visual_cortex = None
        time.sleep(0.5)                     # Wait for the UI to respond
        self.frontal_lobe = None
        self.config = None
        self._config = None
        self.load_config()
        Thalamus()                  # Initialize the Thalamus

    def wake(self):
        """
        Authors : Alix Leroy, SW
        Deeplodocus terminal commands
        :return: None
        """
        self.__on_wake()

        while True:
            command = Notification(DEEP_NOTIF_INPUT, DEEP_MSG_INSTRUCTRION).get()
            try:
                self.__execute_command(command)
            except DeepError:
                time.sleep(0.5)

    def sleep(self):
        """
        Author: SW, Alix Leroy
        Stop the interface, close logs and print good-bye message
        :return: None
        """
        # Stop the visual cortex
        if self.visual_cortex is not None:
            self.visual_cortex.stop()

        self.close_logs()
        End(error=False)

    def save_config(self):
        """
        Author: SW
        Save the config to the config folder
        :return: None
        """
        for key, namespace in self.config.get().items():
            if isinstance(namespace, Namespace):
                namespace.save("%s/%s%s" % (self.config_dir, key, DEEP_EXT_YAML))

    def clear_config(self):
        """
        Author: SW
        Reset the config to an empty Namespace
        :return: None
        """
        self.config = Namespace()

    def restore_config(self):
        """
        Author: SW
        Restore the config to the last stored version
        :return:
        """
        self.config = self._config.copy()

    def store_config(self):
        """
        Author: SW
        Saves a deep copy of the config as _config. In case the user wants to revert to previous settings
        :return: None
        """
        self._config = self.config.copy()

    def load_config(self):
        """
        Author: SW
        Function: Checks current config path is valid, if not, user is prompted to give another
        :return: bool: True if a valid config path is set, otherwise, False
        """
        Notification(DEEP_NOTIF_INFO, DEEP_MSG_LOAD_CONFIG_START % self.config_dir)
        # If the config directory exists
        if os.path.isdir(self.config_dir):
            self.clear_config()
            # For each expected configuration file
            for key, file_name in DEEP_CONFIG_FILES.items():
                config_path = "%s/%s" % (self.config_dir, file_name)
                if os.path.isfile(config_path):
                    self.config.add({key: Namespace(config_path)})
                    Notification(DEEP_NOTIF_SUCCESS, DEEP_MSG_LOAD_CONFIG_FILE % config_path)
                else:
                    Notification(DEEP_NOTIF_ERROR, DEEP_MSG_FILE_NOT_FOUND % config_path)
            self.store_config()
        else:
            Notification(DEEP_NOTIF_ERROR, DEEP_MSG_DIR_NOT_FOUND % self.config_dir)
        #self.check_config()
        self.config.summary()

    def check_config(self):
        """
        AUTHORS:
        --------
        :author: Samuel Westlake

        DESCRIPTION SHORT:
        ------------
        Checks self.config by auto-completing missing parameters with default values and converting values to the
        required data type.
        Once check_config has been run, it can be assumed that self.config is complete.
        See self.__check_config for more details.

        RETURN:
        -------
        :return: None
        """
        self.__check_config()
        Notification(DEEP_NOTIF_SUCCESS, DEEP_MSG_CONFIG_COMPLETE)

    def clear_logs(self, force=False):
        """
        Author: SW
        Deletes logs that are not to be kept, as decided in the config settings
        :param force: bool Use if you want to force delete all logs
        :return: None
        """
        for log_type, (directory, ext) in DEEP_LOGS.items():
            # If forced or log should not be kept, delete the log
            if force or not self.config.project.logs.get(log_type):
                Logs(log_type, directory, ext).delete()

    def close_logs(self, force=False):
        """
        Author: SW
        Closes logs that are to be kept and deletes logs that are to be deleted, as decided in the config settings
        :param force: bool: Use if you want to force all logs to close (use if you don't want logs to be deleted)
        :return: None
        """
        for log_type, (directory, ext) in DEEP_LOGS.items():
            # If forced to closer or log should be kept, close the log
            # NB: config does not have to exist if force is True
            if force or self.config.project.logs.get(log_type):
                if os.path.isfile("%s/%s%s" % (directory, log_type, ext)):
                    Logs(log_type, directory, ext).close()
            else:
                Logs(log_type, directory, ext).delete()

    def ui(self):
        """
        AUTHORS:
        --------AttributeError: module 'asyncio' has no attribute 'create_task'


        :author: Alix Leroy

        DESCRIPTION:
        ------------

        Start the User Interface

        PARAMETERS:AttributeError: module 'asyncio' has no attribute 'create_tasAttributeError: module 'asyncio' has no attribute 'create_task'
k'

        -----------

        None

        RETURN:
        -------

        :return: None
        """

        if self.visual_cortex is None:
            self.visual_cortex = VisualCortex()
        else:
            Notification(DEEP_NOTIF_ERROR, "The Visual Cortex is already running.")

    def stop_ui(self):
        """
        AUTHORS:
        --------

        :author: Alix Leroy

        DESCRIPTION:
        ------------

        Stop the User Interface

        PARAMETERS:
        -----------

        None

        RETURN:
        -------

        :return: None
        """

        if self.visual_cortex is not None:
            self.visual_cortex.stop()
            self.visual_cortex = None
        else:
            Notification(DEEP_NOTIF_ERROR, "The Visual Cortex is already asleep.")

    def __check_config(self, dictionary=DEEP_CONFIG, sub_space=None):
        """
        AUTHORS:
        --------
        :author: Samuel Westlake

        DESCRIPTION:
        ------------
        If a parameter is missing, the user is notified by a DEEP_NOTIF_WARNING with DEEP_MSG_CONFIG_NOT_FOUND.
        The missing parameter is added with the default value specified by DEEP_CONFIG and user is notified of the
        addition of the parameter by a DEEP_NOTIF_WARNING with DEE_MSG_CONFIG_ADDED.
        If a parameter is found successfully, it is converted to the data type specified by 'dtype' in DEEP_CONFIG.
        If a parameter cannot be converted to the required data type, it is replaced with the default from DEEP_CONFIG.

        PARAMETERS:
        -----------
        NB: Both parameters are only for use when check_config calls itself.
        :param dictionary: dictionary to compare self.config with.
        :param sub_space: list of strings defining the path to the current sub-space.

        RETURN:
        -------
        :return: None
        """
        sub_space = [] if sub_space is None else sub_space
        sub_space = sub_space if isinstance(sub_space, list) else [sub_space]
        for key, value in dictionary.items():
            if isinstance(value, dict):
                if "dtype" in value and "default" in value:
                    default = value["default"]
                    if self.config.check(key, sub_space=sub_space):
                        d_type = value["dtype"]
                        current = self.config.get(sub_space)[key]
                        self.config.get(sub_space)[key] = self.__convert_dtype(current,
                                                                               d_type,
                                                                               default,
                                                                               sub_space=sub_space + [key])
                    else:
                        item_path = DEEP_CONFIG_DIVIDER.join(sub_space + [key])
                        Notification(DEEP_NOTIF_WARNING, DEEP_MSG_CONFIG_ADDED % (item_path, default))
                        self.config.get(sub_space)[key] = default
                else:
                    self.__check_config(value, sub_space=sub_space + [key])

    def __convert_dtype(self, value, d_type, default, sub_space=None):
        """
        AUTHORS:
        --------
        :author: Samuel Westlake

        DESCRIPTION:
        ------------
        Converts a given value to a given data type, and returns the result.
        If the value can not be converted, the given default value is returned.
        NB: If d_type is given in a list, e.g. [str], it is assume that value should be a list and each item in value
        will be converted to the given data type. If any item in the list cannot be converted, None will be returned.

        PARAMETERS:
        -----------
        :param value: the value to be converted
        :param d_type: the data type to convert the value to
        :param default: the default value to return if the current value
        :param sub_space: the list of strings that defines the current sub-space

        RETURN:
        -------
        :return: new_value
        """
        sub_space = [] if sub_space is None else sub_space
        if value is None:
            return None
        else:
            try:
                len(d_type)
                d_type = d_type[0]
                is_list = True
            except TypeError:
                is_list = False
            if is_list:
                new_values = []
                value = value if isinstance(value, list) else [value]
                for item in value:
                    new_item = self.__convert(item, d_type)
                    if new_item is not None:
                        new_values.append(new_item)
                    else:
                        Notification(DEEP_NOTIF_WARNING,
                                     DEEP_MSG_NOT_CONVERTED
                                     % (DEEP_CONFIG_DIVIDER.join(sub_space), new_values, d_type, default))
                        return default
                return new_values
            else:
                if d_type == dict:
                    if isinstance(value, Namespace) or value is None:
                        return value
                    else:
                        Notification(DEEP_NOTIF_WARNING, DEEP_MSG_NOT_CONVERTED % (sub_space, value, d_type, default))
                        return Namespace(default)
                else:
                    new_value = self.__convert(value, d_type)
                    if new_value is None:
                        Notification(DEEP_NOTIF_WARNING, DEEP_MSG_NOT_CONVERTED % (sub_space, value, d_type, default))
                        return default
                    else:
                        return new_value

    @staticmethod
    def __convert(value, d_type):
        """
        AUTHORS:
        --------
        :author: Samuel Westlake

        DESCRIPTION:
        ------------
        Converts a given value to a given data type, and returns the result.
        If the value can not be converted, None is returned.

        PARAMETERS:
        -----------
        :param value: the value to be converted.
        :param d_type: the data type to convert the value to.

        RETURN:
        -------
        :return: new_value
        """
        if isinstance(dtype, int) or isinstance(dtype, float):
            try:
                return d_type(eval(value))
            except NameError:
                try:
                    return d_type(value)
                except TypeError:
                    return None
        else:
            try:
                return d_type(value)
            except TypeError:
                return None

    def __on_wake(self):
        """
        AUTHORS:
        --------
        :author: Samuel Westlake

        DESCRIPTION:
        ------------
        Executes the list of commands in self.config.project.on_wake

        RETURN:
        -------
        :return: None
        """
        if self.config.project.on_wake is not None:
            if not isinstance(self.config.project.on_wake, list):
                self.config.project.on_wake = [self.config.project.on_wake]
            for command in self.config.project.on_wake:
                self.__execute_command(command)

    def __execute_command(self, command):
        """
        AUTHORS:
        --------
        :author: Samuel Westlake

        DESCRIPTION:
        ------------
        Calls exec for the given command

        PARAMETERS:
        -----------
        :param command: str: the command to execute

        RETURN:
        -------
        :return: None
        """
        commands, flags = self.__preprocess_command(command)
        for command, flag in zip(commands, flags):
            if command in DEEP_EXIT_FLAGS:
                self.sleep()
            else:
                try:
                    if flag is None:
                        exec("self.%s" % command)
                    elif flag == DEEP_CMD_PRINT:
                        exec("Notification(DEEP_NOTIF_RESULT, self.%s)" % command)
                except DeepError:
                    time.sleep(0.1)

    def __preprocess_command(self, command):
        """
        AUTHORS:
        --------
        :author: Samuel Westlake

        DESCRIPTION:
        ------------
        Pre-processes a given command for execuution.

        PARAMETERS:
        -----------
        :param command: str: the command to process.

        RETURN:
        -------
        :return: str: the command, str: any flags associated with the command.
        """
        commands = command.split(" & ")
        for command in commands:
            remove = False
            for prefix in DEEP_FILTER_STARTS_WITH:
                if command.startswith(prefix):
                    remove = True
                    break
            if not remove:
                for suffix in DEEP_FILTER_ENDS_WITH:
                    if command.endswith(suffix):
                        remove = True
            if not remove:
                for item in DEEP_FILTER:
                    if command == item:
                        remove = True
            if not remove:
                for item in DEEP_FILTER_STARTS_ENDS_WITH:
                    if command.startswith(item) and command.endswith(item):
                        remove = True
            if not remove:
                for item in DEEP_FILTER_INCLUDES:
                    if item in command:
                        remove = True
            if remove:
                commands.remove(command)
                self.__illegal_command_messages(command)
        return self.__get_command_flags(commands)

    @staticmethod
    def __illegal_command_messages(command):
        """
        AUTHORS:
        --------
        :author: Samuel Westlake

        DESCRIPTION:
        ------------
        Explains why a given command is illegal.

        PARAMETERS:
        -----------
        :param command: str: the illegal command.

        RETURN:
        -------
        :return: None
        """
        message = (DEEP_MSG_ILLEGAL_COMMAND % command)
        if "__" in command or "._" in command or command.startswith("_"):
            message = "%s %s" % (message, DEEP_MSG_PRIVATE)
        if command == "wake()":
            message = "%s %s" % (message, DEEP_MSG_ALREADY_AWAKE)
        if command == "config.save":
            message = "%s %s" % (message, DEEP_MSG_USE_CONFIG_SAVE)
        Notification(DEEP_NOTIF_WARNING, message)

    @staticmethod
    def __get_command_flags(commands):
        """
        AUTHORS:
        --------
        :author: Samuel Westlake

        DESCRIPTION:
        ------------
        Extracts any flags from each command in a list of commands.

        PARAMETERS:
        -----------
        :param commands: list of str: the commands to extract flags from.

        RETURN:
        -------
        :return: None
        """
        flags = [None for _ in range(len(commands))]
        for i, command in enumerate(commands):
            for flag in DEEP_CMD_FLAGS:
                if flag in command:
                    flags[i] = flag
                    commands[i] = command.replace(" %s" % flag, "")
                else:
                    flags[i] = None
        return commands, flags

    #
    # ALIASES
    #

    visual_cortex = ui
    vc = ui
    user_interface = ui


brain = None

if __name__ == "__main__":
    import argparse

    def main(args):
        config_dir = args.c
        brain = Brain(config_dir)
        brain.wake()

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", type=str, default="config",
                        help="Path to the config directory")
    arguments = parser.parse_args()
    main(arguments)



