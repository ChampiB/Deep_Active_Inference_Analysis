from copy import deepcopy
import torch
from torch import unsqueeze, nn
from agents.AgentInterface import AgentInterface
from agents.learning import Optimizers
from agents.networks.NetworkFactory import NetworkFactory
from agents.strategies.StrategyFactory import StrategyFactory
from hosts.HostInterface import HostInterface


class DQN(AgentInterface):
    """
    A Deep Q-Network agent
    """

    def __init__(self, json_agent, n_actions):
        """
        Constructor
        :param json_agent: the json describing the agent
        :param n_actions: the number of actions
        """
        super().__init__("DQN")
        self.n_actions = n_actions
        self.queue_capacity = int(json_agent["queue_capacity"])
        self.n_steps_between_synchro = int(json_agent["n_steps_between_synchro"])
        self.q_network_lr = float(json_agent["q_network_lr"])
        self.discount_factor = float(json_agent["discount_factor"])
        self.policy = NetworkFactory.create(json_agent["policy"] | {
            "images_shape": self.image_shape,
            "n_actions": self.n_actions
        })
        self.target = deepcopy(self.policy)
        self.target.eval()
        self.strategy = StrategyFactory.create(json_agent["strategy"])
        HostInterface.to_device([self.policy])
        self.optimizer = Optimizers.get_adam([self.policy], self.q_network_lr)

    def step(self, obs, steps_done):
        """
        Select an action to perform
        :param obs: the observation make
        :param steps_done: the number of training steps done
        :return: the action to take
        """
        # Create a 4D tensor from a 3D tensor by adding a dimension of size one.
        obs = torch.unsqueeze(obs, dim=0)

        # Select an action to perform in the environment.
        return self.strategy.select(self.policy(obs), steps_done)

    def save(self, directory, steps_done):
        """
        Save the agent on the file system
        :param directory: the directory in which to save the agent
        :param steps_done: the number of training steps done
        """
        # Create directories and files if they do not exist.
        checkpoint_file = directory + f"/checkpoint-{steps_done}.pt"
        self.create_dir_and_file(checkpoint_file)

        # Save the model.
        torch.save({
            "agent_module": str(self.__module__),
            "agent_class": str(self.__class__.__name__),
            "images_shape": self.image_shape,
            "n_actions": self.n_actions,
            "policy_net_state_dict": self.policy.state_dict(),
            "policy_net_module": str(self.policy.__module__),
            "policy_net_class": str(self.policy.__class__.__name__),
            "steps_done": steps_done,
            "lr": self.q_network_lr,
            "queue_capacity": self.queue_capacity,
            "discount_factor": self.discount_factor,
            "n_steps_between_synchro": self.n_steps_between_synchro,
            "action_selection": dict(self.strategy)
        }, checkpoint_file)

    def learn(self, logging_file, buffer, steps_done):
        """
        Perform one training iteration
        :param logging_file: the file in which metrics should be saved
        :param buffer: the replay buffer
        :param steps_done: the number of training steps done
        """
        # Synchronize the target network with the policy network if needed
        if steps_done % self.n_steps_between_synchro == 0:
            self.target = deepcopy(self.policy)
            self.target.eval()

        # Sample the replay buffer.
        obs, actions, rewards, done, next_obs = buffer.sample()

        # Compute the policy network's loss function.
        loss = self.compute_loss(logging_file, obs, actions, rewards, done, next_obs, steps_done)

        # Perform one step of gradient descent on the other networks.
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    def compute_loss(self, logging_file, obs, actions, rewards, done, next_obs, steps_done):
        """
        Compute the loss function used to train the policy network.
        :param logging_file: the file in which metrics should be saved
        :param obs: the observations made at time t.
        :param actions: the actions performed at time t.
        :param rewards: the rewards received at time t + 1.
        :param done: did the episode ended after performing action a_t?
        :param next_obs: the observations made at time t + 1.
        :param steps_done: the number of training steps done
        :return: the policy loss.
        """

        # Compute the q-values of the current state and action as predicted by the policy network, i.e. Q(s_t, a_t).
        policy_prediction = self.policy(obs).gather(dim=1, index=unsqueeze(actions.to(torch.int64), dim=1))

        # For each batch entry where the simulation did not stop, compute the value of the next states, i.e. V(s_{t+1}).
        # Those values are computed using the target network.
        future_values = torch.zeros(policy_prediction.shape[0]).to(HostInterface.get_device())
        future_values[torch.logical_not(done)] = self.target(next_obs[torch.logical_not(done)]).max(1)[0]
        future_values = future_values.detach()

        # Compute the expected Q values
        total_values = rewards + future_values * self.discount_factor

        # Compute the loss function.
        loss = nn.SmoothL1Loss()
        loss = loss(policy_prediction, total_values.unsqueeze(1))

        # Print debug information, if needed.
        if steps_done % 10 == 0:
            logging_file.write(str(loss.item()))
        return loss

    def is_model_based(self):
        """
        Check whether the agent is model based or not
        :return: True if the agent is model based, False otherwise
        """
        return False
