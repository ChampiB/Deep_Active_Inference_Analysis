import numpy
from PIL import Image
import os
from agents.AgentInterface import AgentInterface
from agents.inference.TemporalSliceBuilder import TemporalSliceBuilder
from agents.planning.MCTS import MCTS
import torch


class BTAI_3MF(AgentInterface):
    """
    The class implementing the Branching Time Active Inference algorithm with Multi-Modalities and Multi-Factors
    """

    def __init__(self, agent_json, n_actions, env):
        """
        Construct the BTAI_3MF agent
        :param agent_json: the json describing the agent
        :param n_actions: the number of actions in the environment
        :param env: the environment
        """
        super().__init__("BTAI_3MF")
        self.max_planning_steps = int(agent_json["max_planning_steps"])
        self.exp_const = float(agent_json["exp_const"])
        self.n_samples = int(agent_json["n_samples"])
        self.n_actions = n_actions
        self.agent_json = agent_json
        self.env = env
        self.ts = self.create_temporal_slide()
        self.mcts = MCTS(self.exp_const, n_samples=self.n_samples)
        self.last_action = None

    def a(self, noise=0.01):
        """
        Getter.
        :param noise: specify the amount of noise in the prior beliefs.
        :return: the likelihood mappings for each observation.
        """
        env = self.env.unwrapped
        likelihoods = {}
        for x in range(env.width):
            for y in range(env.height):
                likelihood = torch.full([3, env.width, env.height, 2], noise / 2)
                for c in range(2):
                    for xi in range(env.width):
                        for yi in range(env.height):
                            for ci in range(2):
                                if xi == x and yi == y and ci == c:
                                    likelihood[ci][xi][yi][c] = 1 - noise
                                if xi != x or yi != y:
                                    likelihood[2][xi][yi][c] = 1 - noise
                likelihoods[f"O_{x}_{y}"] = likelihood
        return likelihoods

    def b(self, noise=0.01):
        """
        Getter.
        :param noise: specify the amount of noise in the prior beliefs.
        :return: the transitions mappings for each hidden state.
        """
        env = self.env.unwrapped
        transitions = {}

        # Generate the transition matrix of S_color for which action has no effect.
        transition = torch.full([env.s_sizes[2], env.s_sizes[2]], noise / (env.s_sizes[2] - 1))
        for j in range(env.s_sizes[2]):
            transition[j][j] = 1 - noise
        transitions[env.state_names[2]] = transition

        # Generate transitions for which action has an effect.
        for i in range(2):
            transition = torch.full([env.s_sizes[i], env.s_sizes[i], self.n_actions], noise / (env.s_sizes[i] - 1))
            for j in range(env.s_sizes[i]):
                cur_state = torch.zeros([len(env.s_sizes)])
                cur_state[i] = j
                for k in range(self.n_actions):
                    env.x, env.y, env.reward_on_the_right = cur_state[0], cur_state[1], bool(cur_state[2])
                    env.step(k)
                    dest_state = torch.tensor([env.x, env.y, int(env.reward_on_the_right)])
                    dest_id = int(dest_state[i].item())
                    transition[dest_id][j][k] = 1 - noise
            transitions[env.state_names[i]] = transition
        return transitions

    @staticmethod
    def c(noise=0.01):
        """
        Getter.
        :param noise: specify the amount of noise in the prior preferences.
        :return: the prior preferences for each observation.
        """
        preferences = {"O_bottom_left": torch.full([3], noise / 3), "O_bottom_right": torch.full([3], noise / 3)}

        # Create preferences for the bottom right and left corners.
        preferences["O_bottom_left"][0] = 1 - noise
        preferences["O_bottom_right"][1] = 1 - noise
        return preferences

    def d(self, uniform=False, noise=0.01):
        """
        Getter.
        :param uniform: True if the prior over each state should be uniform, False otherwise.
        :param noise: if uniform is False, specify the amount of noise in the prior beliefs.
        :return: the prior over each hidden state.
        """
        env = self.env.unwrapped
        state = env.get_state()
        prior_states = {}
        for i in range(0, len(env.s_sizes)):
            # Create the prior
            if uniform:
                prior = torch.full([env.s_sizes[i]], 1 / env.s_sizes[i])
            else:
                prior = torch.full([env.s_sizes[i]], noise / (env.s_sizes[i] - 1))
                prior[int(state[i])] = 1 - noise

            # Store the prior
            prior_states[env.state_names[i]] = prior
        return prior_states

    def create_temporal_slide(self):
        """
        Create a temporal slice for the mini dSprites environment
        :return: the temporal slide built
        """
        env = self.env.unwrapped
        a = self.a()
        b = self.b()
        c = self.c()
        d = self.d(uniform=True)
        ts_builder = TemporalSliceBuilder("A_0", self.n_actions) \
            .add_state("S_x", d["S_x"]) \
            .add_state("S_y", d["S_y"]) \
            .add_state("S_color", d["S_color"]) \
            .add_transition("S_x", b["S_x"], ["S_x", "A_0"]) \
            .add_transition("S_y", b["S_y"], ["S_y", "A_0"]) \
            .add_transition("S_color", b["S_color"], ["S_color"])
        for i in range(env.width):
            for j in range(env.height):
                ts_builder.add_observation(f"O_{i}_{j}", a[f"O_{i}_{j}"], ["S_x", "S_y", "S_color"])
        ts_builder.add_preference([f"O_{0}_{env.height - 1}"], c["O_bottom_left"])
        ts_builder.add_preference([f"O_{env.width - 1}_{env.height - 1}"], c["O_bottom_right"])
        return ts_builder.build()

    def step(self, obs, steps_done):
        """
        Select an action to perform
        :param obs: the observation make
        :param steps_done: the number of training steps done
        :return: the action to take
        """
        self.ts.reset()
        obs = self.pre_process(obs)
        self.ts.i_step(obs)
        for i in range(0, self.max_planning_steps):
            node = self.mcts.select_node(self.ts)
            e_nodes = self.mcts.expansion(node)
            self.mcts.evaluation(e_nodes)
            self.mcts.propagation(e_nodes)
        action = max(self.ts.children, key=lambda x: x.visits).action
        self.ts = next(filter(lambda x: x.action == action, self.ts.children))
        self.ts.use_posteriors_as_empirical_priors()
        return action

    @staticmethod
    def pre_process(obs):
        """
        Pre-process observation to form a dictionary of variable name to evidence (one-hot) vector
        :param obs: observation
        :return: the dictionary
        """
        res = {}
        for y in range(obs.shape[0]):
            for x in range(obs.shape[1]):
                res[f"O_{x}_{y}"] = obs[y][x] / 255
                if obs[y][x].max() == 0:
                    res[f"O_{x}_{y}"][2] = 1
        return res

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
            Image.fromarray(obs.astype(numpy.uint8)).save(policy_file)

        # Save reconstructed images
        for i, obs in enumerate(observations):
            policy_file = image_directory + f"obs-{i}.png"
            Image.fromarray(obs.astype(numpy.uint8)).save(policy_file)
            obs = self.create_reconstructed_image(obs)
            policy_file = image_directory + f"reconstructed-obs-{i}.png"
            Image.fromarray(obs.astype(numpy.uint8)).save(policy_file)

        # Create directories and files if they do not exist.
        checkpoint_file = directory + f"/checkpoint-{steps_done}.pt"
        self.create_dir_and_file(checkpoint_file)

        # Save the model.
        torch.save({
            "agent_module": str(self.__module__),
            "agent_class": str(self.__class__.__name__),
            "max_planning_steps": self.max_planning_steps,
            "exp_const": self.exp_const,
            "n_actions": self.n_actions,
        }, checkpoint_file)

    def create_reconstructed_image(self, obs):
        """
        Create the reconstructed image:
         - perform I-step to get (states) posterior using input image
         - perform P-step to get (observations) posterior using (states) posterior
         - the observation with the highest probability to create the reconstructed image
        :param obs: the (input) image
        :return: the reconstructed image
        """
        # Compute the posterior distribution over latent state using available observations
        res = numpy.zeros_like(obs)
        self.ts.reset()
        obs = self.pre_process(obs)
        self.ts.i_step(obs)

        # Predict observation from posterior distribution over latent states
        for obs_name in self.ts.obs_posterior.keys():
            self.ts.obs_posterior[obs_name] = self.ts.forward_prediction(
                self.ts.obs_likelihood[obs_name], 0,
                self.ts.obs_parents[obs_name], self.ts.states_posterior
            )

        # Reconstruct image from posterior distribution over observations
        for y in range(res.shape[0]):
            for x in range(res.shape[1]):
                max_obs = self.ts.obs_posterior[f"O_{x}_{y}"].argmax()
                if max_obs <= 1:
                    res[y][x][max_obs] = 255

        return res

    def learn(self, logging_file, buffer, steps_done):
        """
        Perform one training iteration
        :param logging_file: the file in which metrics should be saved
        :param buffer: the replay buffer
        :param steps_done: the number of training steps done
        """
        # Display debug information, if needed.
        # TODO if steps_done % 10 == 0:
        # TODO     logging_file.write(str(vfe_loss.item()))
        # TODO     logging_file.flush()
        pass  # This agent does not learn from data

    def is_model_based(self):
        """
        Check whether the agent is model based or not
        :return: True if the agent is model based, False otherwise
        """
        return True
