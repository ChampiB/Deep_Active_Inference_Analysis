from PIL import Image
from torchvision.utils import save_image
import os
import agents.math.functions as math_fc
import torch
from agents.AgentInterface import AgentInterface
from agents.learning import Optimizers
from agents.networks.NetworkFactory import NetworkFactory
from agents.strategies.StrategyFactory import StrategyFactory
from hosts.HostInterface import HostInterface


class HMM(AgentInterface):
    """
    A Hidden Markov Model agent
    """

    def __init__(self, json_agent, n_actions, *args, **kwargs):
        """
        Constructor
        :param json_agent: the json describing the agent
        :param n_actions: the number of actions
        :param args: the remaining (standard) parameters
        :param kwargs: the remaining (keyword) parameters
        """
        super().__init__("HMM")
        self.n_states = int(json_agent["n_states"])
        self.beta = float(json_agent["beta"])
        self.vfe_lr = float(json_agent["vfe_lr"])
        self.queue_capacity = int(json_agent["queue_capacity"])
        self.n_actions = n_actions
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
        self.strategy = StrategyFactory.create(json_agent["strategy"])
        HostInterface.to_device([self.encoder, self.decoder, self.transition])
        self.optimizer = Optimizers.get_adam([self.encoder, self.decoder, self.transition], self.vfe_lr)

    def step(self, obs, steps_done):
        """
        Select an action to perform
        :param obs: the observation make
        :param steps_done: the number of training steps done
        :return: the action to take
        """
        quality = torch.zeros([1, self.n_actions]).to(HostInterface.get_device())
        return self.strategy.select(quality, steps_done)

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
            "action_selection": dict(self.strategy),
            "lr": self.vfe_lr,
            "beta": self.beta,
            "queue_capacity": self.queue_capacity,
        }, checkpoint_file)

    def learn(self, logging_file, buffer, steps_done):
        """
        Perform one training iteration
        :param logging_file: the file in which metrics should be saved
        :param buffer: the replay buffer
        :param steps_done: the number of training steps done
        """
        # Sample the replay buffer.
        obs, action, _, _, next_obs = buffer.sample()

        # Compute the variational free energy.
        vfe_loss = self.compute_vfe(logging_file, obs, action, next_obs, steps_done)

        # Perform one step of gradient descent on the other networks.
        self.optimizer.zero_grad()
        vfe_loss.backward()
        self.optimizer.step()

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
        kl_div_hs = math_fc.kl_div_gaussian(mean, log_var, mean_hat, log_var_hat)
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
