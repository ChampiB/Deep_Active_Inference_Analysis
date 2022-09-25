import abc
import torch


class HostInterface(abc.ABC):
    """
    An abstract interface that all hosts must implement
    """

    @abc.abstractmethod
    def train(self, agent, env, project_name):
        """
        Train the agent in the environment
        :param agent: the agent
        :param env: the environment
        :param project_name: the name of the project for which the agent is trained
        """
        ...

    @staticmethod
    def get_device():
        """
        Getter
        :return: the device on which computation should be performed
        """
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')
