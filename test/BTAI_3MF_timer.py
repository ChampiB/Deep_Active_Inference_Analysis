import os
import time
from agents.AgentFactory import AgentFactory
from environments.EnvironmentFactory import EnvironmentFactory
from environments.wrappers.DefaultWrappers import DefaultWrappers
from gui.AnalysisConfig import AnalysisConfig


def loop(agent, env):
    """
    Implement the training loop
    :param agent: the agent to train
    :param env: the environment to train
    """
    # Retrieve the initial observation from the environment
    obs = env.reset()
    i = 0
    while i < 1:
        # Select an action
        action = agent.step(obs, i)

        # Execute the action in the environment
        obs, _, done, _ = env.step(action)

        # Reset the environment when a trial ends
        if done:
            obs = env.reset()
        i += 1

    # Close the environment
    env.close()


if __name__ == '__main__':
    # Create the configuration
    data_dir = os.path.dirname(os.path.abspath(__file__)) + "/../data/"
    AnalysisConfig.get(data_directory=data_dir)

    # Compute execution time for MiniSprites environments of different size
    print("Size, Execution time")
    for size in range(2, 21):
        # Create the environment
        env = EnvironmentFactory.create({
            "name": "MiniSprites",
            "module": "environments.impl.MiniSpritesEnvironment",
            "class": "MiniSpritesEnvironment",
            "width": str(size),
            "height": str(size),
            "max_trial_length": "50"
        })

        # Create the agent
        agent = AgentFactory.create({
            "name": "BTAI_3MF",
            "module": "agents.impl.BTAI_3MF",
            "class": "BTAI_3MF",
            "exp_const": "2.4",
            "n_samples": "1",
            "max_planning_steps": "150"
        }, env.action_space.n, env)

        # Apply required wrappers to the environment
        env = DefaultWrappers.apply("BTAI_3MF", env, image_shape=(1, 64, 64))

        # Keep track of the starting time
        start_time = time.time()

        # Run the trials simulation
        loop(agent, env)

        # Keep track of the ending time
        print(f"{size}, {time.time() - start_time}")
