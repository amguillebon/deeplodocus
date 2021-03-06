# Import modules from Python library
from typing import Union
import datetime

# Import modules from deeplodocus
from deeplodocus.callbacks.saver import Saver
from deeplodocus.callbacks.history import History
from deeplodocus.utils.flags import *
from deeplodocus.core.metrics.over_watch_metric import OverWatchMetric
from deeplodocus.utils.generic_utils import generate_random_alphanumeric
Num = Union[int, float]


class Hippocampus(object):
    """
    AUTHORS:
    --------

    :author: Alix Leroy
    :author: Samuel Westlake

    DESCRIPTION:
    ------------

    The Hippocampus class manages all the instances related to the information saved for short and long terms by Deeplodocus

    The following information are handled by the Hippocampus:
        - The history
        - The saving of the model and weights
    """

    def __init__(self,
                 # History
                 losses: dict,
                 metrics: dict,
                 model_name:str = generate_random_alphanumeric(size=10),
                 verbose:int = DEEP_VERBOSE_BATCH,
                 memorize:int = DEEP_MEMORIZE_BATCHES,
                 history_directory: str = DEEP_PATH_HISTORY,
                 overwatch_metric: OverWatchMetric = OverWatchMetric(name=TOTAL_LOSS, condition=DEEP_COMPARE_SMALLER),
                 # Saver
                 save_model_condition:int = DEEP_SAVE_CONDITION_AUTO,
                 save_model_method:int = DEEP_SAVE_NET_FORMAT_PYTORCH,
                 save_model_directory: str = DEEP_PATH_SAVE_MODEL,
                ):

        #
        # HISTORY
        #

        self.__initialize_history(name=model_name,
                                  metrics = metrics,
                                  losses= losses,
                                  log_dir = history_directory,
                                  verbose=verbose,
                                  memorize=memorize,
                                  overwatch_metric=overwatch_metric)

        #
        # SAVER
        #

        self.__initialize_saver(name = model_name,
                                save_directory=save_model_directory,
                                save_condition=save_model_condition,
                                save_method=save_model_method)


    def __initialize_history(self, name: str, metrics, losses, log_dir, verbose, memorize: int, overwatch_metric) -> None:
        """
        Authors : Samuel Westlake, Alix Leroy
        Initialise the history
        :return: None
        """

        timestr = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        train_batches_filename = name + "_history_train_batches_" + timestr + ".csv"
        train_epochs_filename = name + "_history_train_epochs_" + timestr + ".csv"
        validation_filename = name + "_history_validation_" + timestr + ".csv"

        # Initialize the history
        self.history = History(metrics=metrics,
                               losses=losses,
                               log_dir=log_dir,
                               train_batches_filename=train_batches_filename,
                               train_epochs_filename=train_epochs_filename,
                               validation_filename=validation_filename,
                               verbose=verbose,
                               memorize=memorize,
                               overwatch_metric=overwatch_metric)


    def __initialize_saver(self, name: str, save_directory, save_condition, save_method):
        self.saver = Saver(name = name,
                           save_directory=save_directory,
                           save_condition=save_condition,
                           save_method=save_method)


