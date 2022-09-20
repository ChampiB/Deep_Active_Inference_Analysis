import abc


class EnvironmentInterface(abc.ABC):
    """
    An interface all environments must inherit from
    """

    def __init__(self, name):
        """
        Constructor
        :param name: the environment name
        """
        self.name = name
