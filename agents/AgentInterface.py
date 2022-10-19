import abc
import os
from pathlib import Path


class AgentInterface(abc.ABC):
    """
    An interface all agents must inherit from
    """

    def __init__(self, name):
        """
        Constructor
        :param name: the agent name
        """
        self.name = name
        self.image_shape = (1, 64, 64)

    @abc.abstractmethod
    def step(self, obs, steps_done):
        """
        Select an action to perform
        :param obs: the observation make
        :param steps_done: the number of training steps done
        :return: the action to take
        """
        pass

    def collect_observations(self, env):
        """
        Collect observations from the environment
        :param env: the environment
        :return: the pre-processed and real observations
        """
        obs = env.reset()
        observations = [obs]
        real_obs = env.unwrapped.render(mode='rgb_array')
        real_observations = [real_obs]
        i = 0
        done = False
        while done is False and i < 1000:
            # Select an action
            action = self.step(obs, i)

            # Execute the action in the environment
            obs, reward, done, _ = env.step(action)
            observations.append(obs)
            real_obs = env.unwrapped.render(mode='rgb_array')
            real_observations.append(real_obs)

            # Increase index
            i += 1

        return observations, real_observations

    @abc.abstractmethod
    def save(self, directory, steps_done, env):
        """
        Save the agent on the file system
        :param directory: the directory in which to save the agent
        :param steps_done: the number of training steps done
        :param env: the environment to use for gathering reconstructed images and policy demonstration
        """
        pass

    @abc.abstractmethod
    def learn(self, logging_file, buffer, steps_done):
        """
        Perform one training iteration
        :param logging_file: the file in which metrics should be saved
        :param buffer: the replay buffer
        :param steps_done: the number of training steps done
        """
        pass

    @abc.abstractmethod
    def is_model_based(self):
        """
        Check whether the agent is model based or not
        :return: True if the agent is model based, False otherwise
        """
        pass

    @staticmethod
    def create_dir_and_file(checkpoint_file):
        """
        Create the directory and the file corresponding to the checkpoint file passed as parameters
        :param checkpoint_file: the checkpoint file
        """
        checkpoint_dir = os.path.dirname(checkpoint_file)
        if not os.path.exists(checkpoint_dir):
            os.makedirs(checkpoint_dir)
            file = Path(checkpoint_file)
            file.touch(exist_ok=True)

