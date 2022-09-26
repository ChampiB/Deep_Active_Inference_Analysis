import abc
import hashlib

import torch


class HostInterface(abc.ABC):
    """
    An abstract interface that all hosts must implement
    """

    def __init__(self, conf):
        """
        Constructor
        :param conf: the configuration
        """
        self.conf = conf

    @abc.abstractmethod
    def train(self, agent, env, project_name):
        """
        Train the agent in the environment
        :param agent: the agent
        :param env: the environment
        :param project_name: the name of the project for which the agent is trained
        """
        ...

    def get_job_json_path(self, agent, env, project_name):
        """
        Getter
        :param agent: the agent json
        :param env: the environment json
        :param project_name: the project name
        :return: the hash corresponding to the (agent, environment) pair
        """
        hashed = agent + env
        hashed = hashlib.sha224(hashed.encode("utf-8")).hexdigest()
        return self.conf.projects_directory + f"{project_name}/jobs/{hashed}.json"

    @staticmethod
    def get_device():
        """
        Getter
        :return: the device on which computation should be performed
        """
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')
