import gym
from torch import from_numpy


class ToPyTorchTensorWrapper(gym.ObservationWrapper):
    """
    Class turning the images into the format required by pytorch
    """

    def __init__(self, env, device):
        """
        Constructor
        :param env: the environment to be wrapped
        :param device: the device one which the model and tensor should be stored, i.e. GPU or CPU
        """
        super().__init__(env)

        self.device = device

    def observation(self, obs):
        """
        Convert each observation from a numpy array to a Pytorch tensor
        :param obs: the obs stored in a numpy array
        :return: the output observation (pytorch tensor)
        """
        return from_numpy(obs).to(self.device)

