from torch.utils.data import DataLoader
from torch.nn import Module

from deeplodocus.data.dataset import Dataset

class GenericInferer(object):
    """
    AUTHORS:
    --------

    :author: Alix Leroy

    DESCRIPTION:
    ------------

    A GenericInferer class
    """



    def __init__(self,
                 model: Module,
                 dataset: Dataset,
                 batch_size: int = 4,
                 num_workers: int = 4):

        """
        AUTHORS:
        --------

        :author: Alix Leroy

        DESCRIPTION:
        ------------

        Initialize a GenericInferer instance

        PARAMETERS:
        -----------

        :param model->torch.nn.Module: The model to infer
        :param dataset->Dataset: A dataset
        :param batch_size->int: The number of instances per batch
        :param num_workers->int: The number of processes / threads used for data loading
        """

        self.model = model
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.dataset=dataset
        self.dataloader = DataLoader(dataset=dataset,
                                     batch_size=batch_size,
                                     shuffle=False,
                                     num_workers=num_workers)
        self.num_minibatches = self.compute_num_minibatches(batch_size=batch_size,
                                                          length_dataset=dataset.__len__())

    @staticmethod
    def clean_single_element_list(minibatch: list) -> list:
        """
        AUTHORS:
        --------

        :author: Alix Leroy

        DESCRIPTION:
        ------------

        Convert single element lists from the batch into an element

        PARAMETERS:
        -----------

        :param batch->list: The batch to clean

        RETURN:
        -------

        :return cleaned_batch->list: The cleaned batch
        """
        cleaned_minibatch = []

        # For each entry in the minibatch:
        # If it is a single element list -> Make it the single element
        # If it is an empty list -> Make it None
        # Else -> Do not change

        for entry in minibatch:

            if isinstance(entry, list) and len(entry) == 1:
                cleaned_minibatch.append(entry[0])

            elif isinstance(entry, list) and len(entry) == 0:
                cleaned_minibatch.append(None)

            else:
                cleaned_minibatch.append(entry)

        return cleaned_minibatch

    @staticmethod
    def compute_num_minibatches(length_dataset: int, batch_size: int):
        """
        AUTHORS:
        --------

        :author: Alix Leroy

        DESCRIPTION:
        ------------

        Calculate the number of batches for each epoch

        PARAMETERS:
        -----------

        :param length_dataset(int): The length of the dataset
        :param batch_size(int): The number of instances in one mini-batch

        RETURN:
        -------

        :return: None
        """
        if length_dataset % batch_size == 0:
            num_minibatches = length_dataset // batch_size
        else:
            num_minibatches = (length_dataset // batch_size) + 1

        return num_minibatches


    def get_num_minibatches(self):
        """
        AUTHORS:
        --------

        :author: Alix Leroy

        DESCRIPTION:
        ------------

        Getter for self.num_minibatches

        PARAMETERS:
        -----------

        None

        RETURN:
        -------

        :return self.num_minibatches->int: The number of mini batches in the Inferer instance
        """
        return self.num_minibatches

