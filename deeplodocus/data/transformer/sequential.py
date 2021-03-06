from .transformer import Transformer

class Sequential(Transformer):
    """
    AUTHORS:
    --------

    :author: Alix Leroy

    DESCRIPTION:
    ------------

    Sequential class inheriting from Transformer which compute the list of transforms sequentially
    """

    def __init__(self, config):
        """
        AUTHORS:
        --------

        :author: Alix Leroy

        DESCRIPTION:
        ------------

        Initialize a Sequential transformer inheriting a Transformer

        PARAMETERS:
        -----------

        :param config->Namespace: The config

        RETURN:
        -------

        :return: None
        """
        Transformer.__init__(self, config)


    def transform(self, transformed_data, index, data_type):
        """
        AUTHORS:
        --------

        :author: Alix Leroy

        DESCRIPTION:
        ------------

        Transform the data using the Sequential transformer

        PARAMETERS:
        -----------

        :param transformed_data: The data to transform
        :param index: The index of the data
        :param data_type: The data_type

        RETURN:
        -------

        :return transformed_data: The transformed data
        """
        transforms = []

        if self.last_index == index:
            transforms = self.last_transforms

        else:
            # Get mandatory transforms + transforms
            transforms = self.list_mandatory_transforms + self.list_transforms

        # Reinitialize the last transforms
        self.last_transforms = []

        # Apply the transforms
        transformed_data = self.apply_transforms(transformed_data, transforms)

        # Update the last index
        self.last_index = index
        return transformed_data



