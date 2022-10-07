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

    @abc.abstractmethod
    def retrieve_analysis_files(self, job_json):
        """
        Retrieve the analysis files
        :param job_json: the json describing the job whose analysis must be retrieved
        """
        ...

    @staticmethod
    def get_device():
        """
        Getter
        :return: the device on which computation should be performed
        """
        return torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    @staticmethod
    def to_device(models):
        """
        Send the models to the device, i.e. gpu if available or cpu otherwise.
        :param models: the list of model to send to the device.
        :return: nothinh
        """
        for model in models:
            model.to(HostInterface.get_device())
