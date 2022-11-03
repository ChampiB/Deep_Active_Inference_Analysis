from gui.AnalysisConfig import AnalysisConfig


class AgentFactory:
    """
    A factory allowing to create all agents
    """

    conf = None
    agents = None

    @staticmethod
    def create(agent_json, n_actions, env):
        """
        Create an instance of the agent described in the json
        :param agent_json: the json describing the agent
        :param n_actions: the number of actions
        :param env: the environment
        :return: the agent
        """
        if AgentFactory.conf is None:
            AgentFactory.conf = AnalysisConfig.get()
        if AgentFactory.agents is None:
            conf = AgentFactory.conf
            AgentFactory.agents = conf.get_all_classes(conf.agents_directory + "impl/", "agents.impl.")
        agent_class = agent_json["class"]
        return AgentFactory.agents[agent_class](agent_json, n_actions, env)
