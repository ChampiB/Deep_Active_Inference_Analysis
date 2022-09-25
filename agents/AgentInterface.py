import abc


class AgentInterface(abc.ABC):
    """
    An interface all agents must inherit from
    """

    def __init__(self, name):
        """
        Constructor
        :param name: the agent name
        """
        self.name = name

    @abc.abstractmethod
    def step(self, obs):
        """
        Select an action to perform
        :param obs: the observation make
        :return: the action to take
        """
        pass

    @abc.abstractmethod
    def save(self, directory):
        """
        Save the agent on the file system
        :param directory: the directory in which to save the agent
        """
        pass

    @abc.abstractmethod
    def learn(self, logging_file):
        """
        Perform one training iteration
        :param logging_file: the file in which metrics should be saved
        """
        pass

    @abc.abstractmethod
    def is_model_based(self):
        """
        Check whether the agent is model based or not
        :return: True if the agent is model based, False otherwise
        """
        pass
