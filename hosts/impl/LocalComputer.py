import queue
from concurrent.futures import ThreadPoolExecutor as Pool
import train_agent
from gui.AnalysisConfig import AnalysisConfig
from hosts.HostInterface import HostInterface


class LocalComputer(HostInterface):
    """
    A class representing the local computer
    """

    def __init__(self, **kwargs):
        """
        Constructor
        :param kwargs: the remaining arguments
        """
        self.tasks = queue.Queue()
        self.pool = Pool(max_workers=1)
        self.conf = AnalysisConfig.instance

    def run_task(self, x):
        """
        Run the next task in the queue
        :param x: unused
        """
        # Get agent and environment files
        if self.tasks.empty():
            return
        agent, env = self.tasks.get(timeout=1)
        agent_file = self.conf.projects_directory + agent
        env_file = self.conf.projects_directory + env

        # Run the training
        train_agent.train(agent_file, env_file)

    def train(self, agent, env, project_name):
        """
        Train the agent in the environment
        :param agent: the agent
        :param env: the environment
        :param project_name: the name of the project for which the agent is trained
        """
        agent = project_name + f"/agents/{agent}"
        env = project_name + f"/environments/{env}"
        self.tasks.put((agent, env))
        job = self.pool.submit(self.run_task)
        job.add_done_callback(self.run_task)
