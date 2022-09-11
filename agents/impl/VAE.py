from agents.AgentInterface import AgentInterface


class VAE(AgentInterface):
    """
    A Variational Auto-Encoder agent
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__("VAE")
