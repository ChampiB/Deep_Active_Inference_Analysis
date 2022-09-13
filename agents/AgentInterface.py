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
