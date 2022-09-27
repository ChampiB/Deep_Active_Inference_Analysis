import json
import os
from agents.AgentFactory import AgentFactory
from agents.memory.ReplayBuffer import ReplayBuffer, Experience
from environments.EnvironmentFactory import EnvironmentFactory
from environments.wrappers.DefaultWrappers import DefaultWrappers
import numpy as np
import random
import argparse
from gui.AnalysisConfig import AnalysisConfig
import datetime
import torch
from gui.json.Job import Job


def training_loop(agent, env, logging_file, window):
    """
    Implement the training loop
    :param agent: the agent to train
    :param env: the environment to train
    :param logging_file: the file in which to log the agent performance
    :param window: the analysis window if the training is performed locally, None otherwise
    """
    # Create the replay buffer
    buffer = ReplayBuffer()

    # Retrieve the initial observation from the environment
    obs = env.reset()
    total_rewards = 0
    i = 0
    while i < 1000000 and not (window is not None and window.stop_training):
        # Select an action
        action = agent.step(obs)

        # Execute the action in the environment
        old_obs = obs
        obs, reward, done, _ = env.step(action)

        # Add the experience to the replay buffer
        buffer.append(Experience(old_obs, action, reward, done, obs))

        # Perform one iteration of training (if needed)
        if len(buffer) >= 1000:
            agent.learn(logging_file)

        # Save the agent (if needed)
        if i % 10000 == 0:
            agent.save(os.path.dirname(logging_file.name))

        # Monitor total rewards
        total_rewards += reward
        logging_file.write(f"{total_rewards}\n")

        # Reset the environment when a trial ends
        if done:
            obs = env.reset()
        i += 1

    # Close the environment
    env.close()
    return window is not None and window.stop_training


def train(agent_filename, env_filename, window=None):
    """
    Train the agent on the environment
    :param agent_filename: the path to the agent file
    :param env_filename: the path to the environment file
    :param window: the analysis window if the training is performed locally, None otherwise
    """
    # Set the project seed
    seed = 0
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)

    # Create the configuration
    data_dir = os.path.dirname(os.path.abspath(__file__)) + "/data/"
    AnalysisConfig.get(data_directory=data_dir)

    # Create the environment and apply standard wrappers
    env_file = open(env_filename, "r")
    env_json = json.load(env_file)
    env = EnvironmentFactory.create(env_json)
    env = DefaultWrappers.apply(env, image_shape=(1, 64, 64))

    # Create the agent
    agent_file = open(agent_filename, "r")
    agent_json = json.load(agent_file)
    agent = AgentFactory.create(agent_json)

    # Create the logging file
    logging_dir = data_dir + f"logging/{env_json['name']}/{agent_json['name']}/"
    if not os.path.exists(logging_dir):
        os.makedirs(logging_dir)
    logging_file = open(logging_dir + "results.csv", "w+")

    # Write the csv header
    logging_file.write("vfe,reward\n" if agent.is_model_based() else "reward\n")

    # Keep track of the starting time
    job_file = open(logging_dir + "job.csv", "w+")
    job_file.write("starting_time,hardware,ending_time\n")
    job_file.write(f"{datetime.datetime.now()},")

    # Keep track of hardware
    hardware = f"gpu[{torch.cuda.get_device_name()}," if torch.cuda.is_available() else "cpu,"
    job_file.write(hardware)

    # Train the agent on the environment (keep track of the training time)
    stop_training = training_loop(agent, env, logging_file, window)

    # Update the job status
    if stop_training and window is not None:

        # Get json path
        path = agent_filename.split("/")
        project_name = path[-3]
        agent = path[-1]
        env = env_filename.split("/")[-1]

        # Update the job
        job = Job(window.filesystem_mutex, agent, env, project_name)
        job.update("status", "crashed")
        window.stop_training = False
        exit(0)
    else:
        print("Agent trained successfully!", flush=True)

    # Keep track of the ending time
    job_file.write(f"{datetime.datetime.now()}\n")


if __name__ == '__main__':
    # Parse program arguments
    parser = argparse.ArgumentParser(description='Train an agent on an environment.')
    parser.add_argument('agent_file', type=str, help='the path to the agent file')
    parser.add_argument('env_file', type=str, help='the path to the environment file')
    args = parser.parse_args()

    # Keep track of GPU used
    print(f"GPU: {torch.cuda.get_device_name(torch.cuda.current_device())}", flush=True)

    # Train the agent
    train(args.agent_file, args.env_file)
