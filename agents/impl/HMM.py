from agents.AgentInterface import AgentInterface


class HMM(AgentInterface):
    """
    A Hidden Markov Model agent
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__("HMM")
