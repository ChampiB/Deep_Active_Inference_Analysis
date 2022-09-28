import threading
from datetime import datetime
import train_agent
from gui.DataStorage import DataStorage
from gui.jobs.Job import Job
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
        self.tool = DataStorage.get("tool")
        self.window = DataStorage.get("window")
        self.conf = DataStorage.get("conf")

    def run_task(self, job):
        """
        Run the next task in the queue
        :param job: the jib to run
        """
        # Check whether to start the task
        stopping_key = job.json["env"] + "/" + job.json["agent"]
        stopping_key = stopping_key.replace("ALE_", "")
        if self.window.stop_training or stopping_key in self.window.jobs_to_stop:
            self.window.jobs_to_stop.remove(stopping_key)
            return

        # Get agent and environment files
        if self.window.tasks.empty():
            return
        agent, env, project_name = self.window.tasks.get(timeout=1)
        agent_file = self.conf.projects_directory + agent
        env_file = self.conf.projects_directory + env

        # Run the training
        job.update("status", "running", save=False)
        job.update("start_time", datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
        try:
            train_agent.train(agent_file, env_file, self.window)
            job.update("status", "success")
        except Exception as e:
            print(e)
            job.update("status", "crashed")

    def train(self, agent, env, project_name):
        """
        Train the agent in the environment
        :param agent: the agent
        :param env: the environment
        :param project_name: the name of the project for which the agent is trained
        """
        job = Job.create_on_local_computer(self.window.filesystem_mutex, agent, env, project_name, {
            "host": "local computer",
            "hardware": "cpu"
        })
        if job is None:
            return
        agent = project_name + f"/agents/{agent}"
        env = project_name + f"/environments/{env}"
        self.window.tasks.put((agent, env, project_name))
        job = self.window.pool.submit(self.run_task, job)
        self.window.jobs.append(job)
        threading.Thread(target=lambda j=job: j.result()).start()
