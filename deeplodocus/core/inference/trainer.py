#
# BACKEND IMPORTS
#
from torch.nn import Module

#
# DEEPLODOCUS IMPORTS
#

from deeplodocus.data.dataset import Dataset
from deeplodocus.callbacks.callback import Callback
from deeplodocus.core.inference.tester import Tester
from deeplodocus.utils.notification import Notification
from deeplodocus.utils.dict_utils import apply_weight
from deeplodocus.utils.dict_utils import sum_dict
from deeplodocus.utils.flags import *
from deeplodocus.utils.generic_utils import is_string_an_integer
from deeplodocus.core.inference.generic_evaluator import GenericEvaluator


class Trainer(GenericEvaluator):

    def __init__(self,
                 model: Module,
                 dataset: Dataset,
                 metrics: dict,
                 losses: dict,
                 optimizer,
                 num_epochs: int,
                 initial_epoch: int = 1,
                 batch_size: int = 4,
                 shuffle: int = DEEP_SHUFFLE_ALL,
                 num_workers: int = 4,
                 verbose: int=DEEP_VERBOSE_BATCH,
                 data_to_memorize: int = DEEP_MEMORIZE_BATCHES,
                 save_condition: int=DEEP_SAVE_CONDITION_AUTO,
                 stopping_parameters=None,
                 tester: Tester=None,
                 model_name: str = "test",
                 write_logs=True):
        """
        AUTHORS:
        --------

        :author: Alix Leroy

        DESCRIPTION:
        ------------

        Initialize a Trainer instance

        PARAMETERS:
        -----------

        :param model->torch.nn.Module: The model which has to be trained
        :param dataset->Dataset: The dataset to be trained on
        :param metrics->dict: The metrics to analyze
        :param losses->dict: The losses to use for the backpropagation
        :param optimizer: The optimizer to use for the backpropagation
        :param num_epochs->int: Number of epochs for the training
        :param initial_epoch->int: The index of the initial epoch
        :param batch_size->int: Size a minibatch
        :param shuffle->int: DEEP_SHUFFLE flag, method of shuffling to use
        :param num_workers->int: Number of processes / threads to use for data loading
        :param verbose->int: DEEP_VERBOSE flag, How verbose the Trainer is
        :param data_to_memorize->int: DEEP_MEMORIZE flag, what data to save
        :param save_condition->int: DEEP_SAVE flag, when to save the results
        :param stopping_parameters:
        :param tester->Tester: The tester to use for validation
        :param model_name->str: The name of the model
        :param write_logs->bool: Whether to write the logs or not

        RETURN:
        -------

        :return: None
        """

        # Initialize the GenericEvaluator par
        super().__init__(model=model,
                         dataset=dataset,
                         metrics=metrics,
                         losses=losses,
                         batch_size=batch_size,
                         num_workers=num_workers,
                         verbose=verbose)

        # Create callbacks
        self.callbacks = Callback(metrics=metrics,
                                  losses=losses,
                                  working_directory="",
                                  model_name=model_name,
                                  verbose=verbose,
                                  data_to_memorize=data_to_memorize,
                                  save_condition=save_condition,
                                  stopping_parameters=stopping_parameters,
                                  write_logs=write_logs)

        self.write_logs = write_logs
        self.shuffle = shuffle
        self.optimizer = optimizer
        self.initial_epoch = initial_epoch
        self.num_epochs = num_epochs

        if isinstance(tester, Tester):
            self.tester = tester          # Tester for validation
            self.tester.set_metrics(metrics=metrics)
            self.tester.set_losses(losses=losses)
        else:
            self.tester = None

    def fit(self, first_training: bool = True)->None:
        """
        :param first_training:
        :return:
        """
        self.__train(first_training=first_training)
        Notification(DEEP_NOTIF_SUCCESS, FINISHED_TRAINING, write_logs=self.write_logs)
        # Prompt if the user want to continue the training
        self.__continue_training()

    def __train(self, first_training=True)->None:
        """
        AUTHORS:
        --------

        :author: Alix Leroy

        DESCRIPTION:
        ------------

        Loop over the dataset to train the network

        PARAMETERS:
        -----------

        :param first_training->bool: Whether more epochs have been required after initial training or not

        RETURN:
        -------

        :return: None
        """

        if first_training is True:
            self.callbacks.on_train_begin()

        for epoch in range(self.initial_epoch, self.num_epochs+1):  # loop over the dataset multiple times
            self.callbacks.on_epoch_start(epoch_index=epoch, num_epochs=self.num_epochs)
            for minibatch_index, minibatch in enumerate(self.dataloader):

                # Clean the given data
                inputs, labels, additional_data = self.clean_single_element_list(minibatch)

                # zero the parameter gradients
                self.optimizer.zero_grad()

                # Infer the output of the batch
                outputs = self.model(inputs)

                # Compute losses and metrics
                result_losses = self.compute_metrics(self.losses, inputs, outputs, labels, additional_data)
                result_metrics = self.compute_metrics(self.metrics, inputs, outputs, labels, additional_data)

                # Add weights to losses
                result_losses = apply_weight(result_losses, self.losses)

                # Sum all the result of the losses
                total_loss = sum_dict(result_losses)

                # Accumulates the gradient (by addition) for each parameter
                total_loss.backward()

                # Performs a parameter update based on the current gradient (stored in .grad attribute of a parameter) and the update rule
                self.optimizer.step()

                # Mini batch callback
                self.callbacks.on_batch_end(minibatch_index=minibatch_index+1,
                                            num_minibatches=self.num_minibatches,
                                            epoch_index=epoch,
                                            total_loss=total_loss.item(),
                                            result_losses=result_losses,
                                            result_metrics=result_metrics)

            # Shuffle the data if required
            if self.shuffle is not None:
                self.dataset.shuffle(self.shuffle)

            # Reset the dataset (transforms cache)
            self.dataset.reset()

            # Evaluate the model
            total_validation_loss, result_validation_losses, result_validation_metrics = self.__evaluate_epoch()

            # Epoch callback
            self.callbacks.on_epoch_end(epoch_index=epoch,
                                        num_epochs=self.num_epochs,
                                        model=self.model,
                                        num_minibatches=self.num_minibatches,
                                        total_validation_loss=total_validation_loss.item(),
                                        result_validation_losses=result_validation_losses,
                                        result_validation_metrics=result_validation_metrics,
                                        num_minibatches_validation=self.tester.get_num_minibatches())
        # End of training callback
        self.callbacks.on_training_end(model=self.model)
        # Pause callbacks which compute time
        self.callbacks.pause()

    def __continue_training(self):
        """
        :return:
        """
        continue_training = ""
        # Ask if the user want to continue the training
        while continue_training.lower() not in ["y", "n"]:
            continue_training = Notification(DEEP_NOTIF_INPUT, "Would you like to continue the training ? (Y/N) ",
                                             write_logs=self.write_logs).get()
        # If yes ask the number of epochs
        if continue_training.lower() == "y":
            while True:
                epochs = Notification(DEEP_NOTIF_INPUT, "Number of epochs ? ", write_logs=self.write_logs).get()
                try:
                    epochs = int(epochs)
                    break
                except ValueError:
                    Notification(DEEP_NOTIF_WARNING, "Number of epochs must be an integer",
                                 write_logs=self.write_logs).get()
            if epochs > 0:
                self.initial_epoch = self.num_epochs + 1
                self.num_epochs += epochs
                # Resume the training
                self.fit(first_training=False)
        else:
            pass

    def __evaluate_epoch(self):
        """
        :return:
        """
        total_validation_loss = None
        result_losses = None
        result_metrics = None
        if self.tester is not None:
            total_validation_loss, result_losses, result_metrics = self.tester.evaluate()
        return total_validation_loss, result_losses, result_metrics