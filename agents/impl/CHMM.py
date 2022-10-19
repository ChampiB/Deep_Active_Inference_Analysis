from PIL import Image
from torchvision.utils import save_image
import os
from copy import deepcopy
import agents.math.functions as math_fc
import torch
from torch import unsqueeze, nn
from agents.AgentInterface import AgentInterface
from agents.learning import Optimizers
from agents.networks.NetworkFactory import NetworkFactory
from agents.strategies.StrategyFactory import StrategyFactory
from hosts.HostInterface import HostInterface


class CHMM(AgentInterface):
    """
    A Critical Hidden Markov Model agent
    """

    def __init__(self, json_agent, n_actions):
        """
        Constructor
        :param json_agent: the json describing the agent
        :param n_actions: the number of actions
        """
        super().__init__("CHMM")
        self.n_states = int(json_agent["n_states"])
        self.beta = float(json_agent["beta"])
        self.vfe_lr = float(json_agent["vfe_lr"])
        self.critic_lr = float(json_agent["critic_lr"])
        self.queue_capacity = int(json_agent["queue_capacity"])
        self.n_actions = n_actions
        self.discount_factor = float(json_agent["discount_factor"])
        self.n_steps_between_synchro = int(json_agent["n_steps_between_synchro"])
        self.g_value = json_agent["critic_objective"]
        self.encoder = NetworkFactory.create(json_agent["encoder"] | {
            "n_states": self.n_states,
            "image_shape": self.image_shape
        })
        self.decoder = NetworkFactory.create(json_agent["decoder"] | {
            "n_states": self.n_states,
            "image_shape": self.image_shape
        })
        self.transition = NetworkFactory.create(json_agent["transition"] | {
            "n_states": self.n_states,
            "n_actions": self.n_actions
        })
        self.critic = NetworkFactory.create(json_agent["critic"] | {
            "n_states": self.n_states,
            "n_actions": self.n_actions
        })
        self.target = deepcopy(self.critic)
        self.target.eval()
        self.strategy = StrategyFactory.create(json_agent["strategy"])
        HostInterface.to_device([self.encoder, self.decoder, self.transition])
        self.vfe_optimizer = Optimizers.get_adam([self.encoder, self.decoder, self.transition], self.vfe_lr)
        self.efe_optimizer = Optimizers.get_adam([self.critic], self.critic_lr)

    def step(self, obs, steps_done):
        """
        Select an action to perform
        :param obs: the observation make
        :param steps_done: the number of training steps done
        :return: the action to take
        """
        # Extract the current state from the current observation.
        obs = torch.unsqueeze(obs, dim=0)
        state, _ = self.encoder(obs)

        # Select an action.
        return self.strategy.select(self.critic(state)[:, :self.n_actions], steps_done)

    def save(self, directory, steps_done, env):
        """
        Save the agent on the file system
        :param directory: the directory in which to save the agent
        :param steps_done: the number of training steps done
        :param env: the environment to use for gathering reconstructed images and policy demonstration
        """
        # Gather the observations and create image directory
        observations, real_observations = self.collect_observations(env)
        image_directory = directory + f"/{steps_done}/"
        if not os.path.exists(image_directory):
            os.makedirs(image_directory)

        # Save policy
        for i, obs in enumerate(real_observations):
            policy_file = image_directory + f"real-obs-{i}.png"
            Image.fromarray(obs).save(policy_file)

        # Save reconstructed images
        for i, obs in enumerate(observations):
            policy_file = image_directory + f"obs-{i}.png"
            save_image(obs, policy_file)
            mean, log_var = self.encoder(obs.unsqueeze(axis=0))
            obs = self.decoder(math_fc.re_parameterize(mean, log_var))
            policy_file = image_directory + f"reconstructed-obs-{i}.png"
            save_image(obs, policy_file)
            # TODO sequence of actions

        # Create directories and files if they do not exist.
        checkpoint_file = directory + f"/checkpoint-{steps_done}.pt"
        self.create_dir_and_file(checkpoint_file)

        # Save the model.
        torch.save({
            "agent_module": str(self.__module__),
            "agent_class": str(self.__class__.__name__),
            "images_shape": self.image_shape,
            "n_states": self.n_states,
            "n_actions": self.n_actions,
            "decoder_net_state_dict": self.decoder.state_dict(),
            "decoder_net_module": str(self.decoder.__module__),
            "decoder_net_class": str(self.decoder.__class__.__name__),
            "encoder_net_state_dict": self.encoder.state_dict(),
            "encoder_net_module": str(self.encoder.__module__),
            "encoder_net_class": str(self.encoder.__class__.__name__),
            "transition_net_state_dict": self.transition.state_dict(),
            "transition_net_module": str(self.transition.__module__),
            "transition_net_class": str(self.transition.__class__.__name__),
            "critic_net_state_dict": self.critic.state_dict(),
            "critic_net_module": str(self.critic.__module__),
            "critic_net_class": str(self.critic.__class__.__name__),
            "beta": self.beta,
            "g_value": self.g_value,
            "vfe_lr": self.vfe_lr,
            "efe_lr": self.critic_lr,
            "discount_factor": self.discount_factor,
            "queue_capacity": self.queue_capacity,
            "n_steps_between_synchro": self.n_steps_between_synchro,
            "action_selection": dict(self.strategy),
        }, checkpoint_file)

    def learn(self, logging_file, buffer, steps_done):
        """
        Perform one training iteration
        :param logging_file: the file in which metrics should be saved
        :param buffer: the replay buffer
        :param steps_done: the number of training steps done
        """
        # Synchronize the target with the critic (if needed).
        if steps_done % self.n_steps_between_synchro == 0:
            self.target = deepcopy(self.critic)
            self.target.eval()

        # Sample the replay buffer.
        obs, actions, rewards, done, next_obs = buffer.sample()

        # Compute the expected free energy loss.
        efe_loss = self.compute_efe_loss(logging_file, obs, actions, next_obs, done, rewards)

        # Perform one step of gradient descent on the critic network.
        self.efe_optimizer.zero_grad()
        efe_loss.backward()
        self.efe_optimizer.step()

        # Compute the variational free energy.
        vfe_loss = self.compute_vfe(logging_file, obs, actions, next_obs, steps_done)

        # Perform one step of gradient descent on the other networks.
        self.vfe_optimizer.zero_grad()
        vfe_loss.backward()
        self.vfe_optimizer.step()

    def compute_efe_loss(self, config, obs, actions, next_obs, done, rewards):
        """
        Compute the expected free energy loss
        :param config: the hydra configuration
        :param obs: the observations at time t
        :param actions: the actions at time t
        :param next_obs: the observations at time t + 1
        :param done: did the simulation ended at time t + 1 after performing the actions at time t
        :param rewards: the rewards at time t + 1
        :return: expected free energy loss
        """
        # Compute required vectors.
        mean_hat_t, log_var_hat_t = self.encoder(obs)
        mean, log_var = self.transition(mean_hat_t, actions)
        mean_hat, log_var_hat = self.encoder(next_obs)

        # Compute the G-values of each action in the current state.
        critic_prediction = self.critic(mean_hat_t)
        critic_prediction = critic_prediction.gather(dim=1, index=unsqueeze(actions.to(torch.int64), dim=1))

        # For each batch entry where the simulation did not stop, compute the value of the next states.
        future_g_value = torch.zeros(critic_prediction.shape[0], device=HostInterface.get_device())
        future_g_value[torch.logical_not(done)] = self.target(mean_hat[torch.logical_not(done)]).max(1)[0]

        # Compute the immediate G-value.
        immediate_g_value = rewards

        # Add information gain to the immediate g-value (if needed).
        immediate_g_value -= math_fc.compute_info_gain(self.g_value, mean_hat, log_var_hat, mean, log_var)

        immediate_g_value = immediate_g_value.to(torch.float32)

        # Compute the discounted G values.
        g_value = immediate_g_value + self.discount_factor * future_g_value
        g_value = g_value.detach()

        # Compute the loss function.
        loss = nn.SmoothL1Loss()
        loss = loss(critic_prediction, g_value.unsqueeze(dim=1))
        return loss

    def compute_vfe(self, logging_file, obs, actions, next_obs, steps_done):
        """
        Compute the variational free energy
        :param logging_file: the file in which metrics should be saved
        :param obs: the observations at time t
        :param actions: the actions at time t
        :param next_obs: the observations at time t + 1
        :param steps_done: the number of training steps done
        :return: the variational free energy
        """
        # Compute required vectors.
        mean_hat, log_var_hat = self.encoder(obs)
        states = math_fc.re_parameterize(mean_hat, log_var_hat)
        mean_hat, log_var_hat = self.encoder(next_obs)
        next_state = math_fc.re_parameterize(mean_hat, log_var_hat)
        mean, log_var = self.transition(states, actions)
        alpha = self.decoder(next_state)

        # Compute the variational free energy.
        kl_div_hs = math_fc.kl_div_gaussian(mean_hat, log_var_hat, mean, log_var)
        log_likelihood = math_fc.log_bernoulli_with_logits(next_obs, alpha)
        vfe_loss = self.beta * kl_div_hs - log_likelihood

        # Display debug information, if needed.
        if steps_done % 10 == 0:
            logging_file.write(str(vfe_loss.item()))
            logging_file.flush()
        return vfe_loss

    def is_model_based(self):
        """
        Check whether the agent is model based or not
        :return: True if the agent is model based, False otherwise
        """
        return True
