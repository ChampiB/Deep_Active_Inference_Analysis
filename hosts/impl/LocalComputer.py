import json
import os.path
import queue
import threading
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
        self.conf = AnalysisConfig.instance
        self.tasks = queue.Queue()
        self.pool = Pool(max_workers=1)

    def run_task(self):
        """
        Run the next task in the queue
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
        # Get json path
        json_path = self.get_job_json_path(agent, env, project_name)

        # Check if job should be re-run
        if os.path.exists(json_path):
            job = json.load(open(json_path, "r"))
            if job["status"] != "crashed":
                return

        # Launch a new job
        file = open(json_path, mode="w+")
        json.dump({
            "agent": agent,
            "env": env,
            "status": "pending",
            "host": "local computer",
            "hardware": "cpu",
        }, file, indent=2)
        agent = project_name + f"/agents/{agent}"
        env = project_name + f"/environments/{env}"
        self.tasks.put((agent, env))
        job = self.pool.submit(self.run_task)
        threading.Thread(target=lambda j: j.result(), args=(job,)).start()
