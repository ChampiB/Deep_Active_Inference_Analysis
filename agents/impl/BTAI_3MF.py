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
        self.max_planning_steps = agent_json["max_planning_steps"]
        self.exp_const = agent_json["exp_const"]
        self.n_actions = n_actions
        self.env = env
        self.ts = self.create_temporal_slide()
        self.mcts = MCTS(self.exp_const)
        self.last_action = None

    def a(self, noise=0.001):
        """
        Getter.
        :param noise: specify the amount of noise in the prior beliefs.
        :return: the likelihood mappings for each observation.
        """
        env = self.env.unwrapped
        likelihoods = {}
        for i in range(env.s_sizes.size):
            epsilon = noise / (env.s_sizes[i] - 1) if env.s_sizes[i] != 1 else 0
            likelihood = torch.full([env.s_sizes[i], env.s_sizes[i]], epsilon)
            for j in range(env.s_sizes[i]):
                likelihood[j][j] = 1 - noise if env.s_sizes[i] != 1 else 1
            likelihoods[env.obs_names[i]] = likelihood
        return likelihoods

    def b(self, noise=0.001):
        """
        Getter.
        :param noise: specify the amount of noise in the prior beliefs.
        :return: the transitions mappings for each hidden state.
        """
        env = self.env.unwrapped
        transitions = {}

        # Generate transitions for which action has no effect.
        for i in range(1, 4):
            transition = torch.full([env.s_sizes[i], env.s_sizes[i]], noise / (envs_sizes[i] - 1))
            for j in range(env.s_sizes[i]):
                transition[j][j] = 1 - noise
            transitions[env.state_names[i]] = transition

        # Generate transitions for which action has an effect.
        for i in range(4, env.s_sizes.size):
            transition = torch.full([env.s_sizes[i], env.s_sizes[i], env.n_actions], noise / (env.s_sizes[i] - 1))
            for j in range(env.s_sizes[i]):
                cur_state = torch.zeros([env.s_sizes.size])
                cur_state[i] = j * env.granularity
                for k in range(self.n_actions):
                    dest_state = env.simulate(k, cur_state)
                    dest_id = int(dest_state[i].item() / env.granularity)
                    transition[dest_id][j][k] = 1 - noise
            transitions[env.state_names[i]] = transition
        return transitions

    def c(self):
        """
        Getter.
        :return: the prior preferences for each observation.
        """
        env = self.env.unwrapped
        preferences = {}

        # Create preferences for observations over which no outcome is preferred.
        for i in [0, 2, 3]:
            preferences[env.obs_names[i]] = torch.full([env.s_sizes[i]], 1 / env.s_sizes[i])

        # Create preferences for the shape and x position of the object.
        preference = torch.zeros([env.s_sizes[4], env.s_sizes[5], env.s_sizes[1]])
        for shape in range(0, 3):
            start_pos = 1 if shape == 0 else 0  # If shape == square then 1 else 0
            end_pos = env.n_pos if shape == 0 else env.n_pos - 1  # If shape == square then n_pos else n_pos-1
            y_pos = int(32 / env.granularity)
            for x_pos in range(start_pos, int(end_pos)):
                preference[x_pos][y_pos][shape] = -5
            if shape == 0:
                preference[0][y_pos][shape] = 5
            else:
                preference[int(env.n_pos - 1)][y_pos][shape] = 5
        shape = preference.shape
        preference = torch.softmax(preference.view(-1), dim=0).view(shape)
        preferences[env.obs_names[1] + "_pos_x_y"] = preference

        # Create preferences over the y position.
        noise = 0.6
        preference = torch.full([env.s_sizes[5]], noise / (env.s_sizes[5] - 1))
        preference[env.s_sizes[5] - 1] = 1 - noise
        preferences[env.obs_names[5]] = preference

        return preferences

    def d(self, uniform=False, noise=0.001):
        """
        Getter.
        :param uniform: True if the prior over each state should be uniform, False otherwise.
        :param noise: if uniform is False, specify the amount of noise in the prior beliefs.
        :return: the prior over each hidden state.
        """
        env = self.env.unwrapped
        state = env.get_state()
        prior_states = {}
        for i in range(1, env.s_sizes.size):
            if uniform:
                prior = torch.full([env.s_sizes[i]], 1 / env.s_sizes[i])
                prior_states[env.state_names[i]] = prior
            else:
                prior = torch.full([env.s_sizes[i]], noise / (env.s_sizes[i] - 1))
                prior[int(state[i])] = 1 - noise
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
        d = self.d()
        ts_builder = TemporalSliceBuilder("A_0", self.n_actions) \
            .add_state("S_x", d["S_x"]) \
            .add_state("S_y", d["S_y"]) \
            .add_state("S_color", d["S_color"]) \
            .add_transition("S_x", b["S_x"], ["S_x", "A_0"]) \
            .add_transition("S_y", b["S_y"], ["S_y", "A_0"]) \
            .add_transition("S_color", b["S_color"], ["S_color"])
        for i in range(env.width):
            for j in range(env.height):
                ts_builder.add_observation(f"O_pos_{i}_{i}", a[f"O_pos_{i}_{i}"], ["S_x", "S_y", "S_color"])
            .add_preference(["O_pos_x", "O_pos_y", "O_shape"], c["O_shape_pos_x_y"]) \
        return ts_builder.build()

    def step(self, obs, steps_done):
        """
        Select an action to perform
        :param obs: the observation make
        :param steps_done: the number of training steps done
        :return: the action to take
        """
        self.ts.reset()
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

    def save(self, directory, steps_done, env):
        pass  # TODO

    def learn(self, logging_file, buffer, steps_done):
        """
        Perform one training iteration
        :param logging_file: the file in which metrics should be saved
        :param buffer: the replay buffer
        :param steps_done: the number of training steps done
        """
        pass  # This agent does not learn from data

    def is_model_based(self):
        """
        Check whether the agent is model based or not
        :return: True if the agent is model based, False otherwise
        """
        return True

