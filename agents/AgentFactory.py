from gui.AnalysisConfig import AnalysisConfig


class AgentFactory:
    """
    A factory allowing to create all agents
    """

    conf = None
    agents = None

    @staticmethod
    def create(json_agent, n_actions):
        """
        Create an instance of the agent described in the json
        :param json_agent: the json
        :param n_actions: the number of actions
        :return: the agent
        """
        if AgentFactory.conf is None:
            AgentFactory.conf = AnalysisConfig.get()
        if AgentFactory.agents is None:
            conf = AgentFactory.conf
            AgentFactory.agents = conf.get_all_classes(conf.agents_directory + "impl/", "agents.impl.")
        agent_class = json_agent["class"]
        return AgentFactory.agents[agent_class](json_agent, n_actions)
