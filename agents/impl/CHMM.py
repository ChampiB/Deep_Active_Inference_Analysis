from agents.AgentInterface import AgentInterface


class CHMM(AgentInterface):
    """
    A Critical Hidden Markov Model agent
    """

    def __init__(self, json_agent):
        """
        Constructor
        :param json_agent: the json describing the agent
        """
        super().__init__("CHMM")

    def step(self, obs):
        """
        Select an action to perform
        :param obs: the observation make
        :return: the action to take
        """
        # TODO
        return 0

    def save(self, directory):
        """
        Save the agent on the file system
        :param directory: the directory in which to save the agent
        """
        # TODO
        pass

    def learn(self, logging_file):
        """
        Perform one training iteration
        :param logging_file: the file in which metrics should be saved
        """
        # TODO
        pass

    def is_model_based(self):
        """
        Check whether the agent is model based or not
        :return: True if the agent is model based, False otherwise
        """
        return True
