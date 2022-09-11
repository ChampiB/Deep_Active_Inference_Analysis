from agents.AgentInterface import AgentInterface


class DQN(AgentInterface):
    """
    A Deep Q-Network agent
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__("DQN")
