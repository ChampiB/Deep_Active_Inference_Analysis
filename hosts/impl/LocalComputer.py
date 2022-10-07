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
        }, forward_mutex=False)
        if job is None:
            return
        agent = project_name + f"/agents/{agent}"
        env = project_name + f"/environments/{env}"
        self.window.pool.submit(job, agent=agent, env=env, projects_directory=self.conf.projects_directory)

    def retrieve_analysis_files(self, job_json):
        """
        Retrieve the analysis files
        :param job_json: the json describing the job whose analysis must be retrieved
        """
        pass
