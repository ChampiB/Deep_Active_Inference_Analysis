import gym
from environments.impl.SpritesEnvironment import SpritesEnvironment


class EnvironmentFactory:
    """
    A factory allowing to create all environments
    """

    @staticmethod
    def create(json_env):
        """
        Create an instance of the environment described in the json
        :param json_env: the json
        :return: the environment
        """
        if json_env["class"] == "SpritesEnvironment":
            return SpritesEnvironment(json_env)
        if json_env["class"] == "OpenAI":
            return gym.make(json_env["name"])
        print(f"Environment '{json_env}' is not supported.")
