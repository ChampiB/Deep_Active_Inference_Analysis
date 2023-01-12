import copy

from torch import nn
from PIL import Image
from agents.math.functions import kl_div_categorical
import math
import queue
import torch
import random
import numpy as np
from torch.nn.functional import one_hot
from agents.inference.Operators import Operators
from agents.inference.enum.InferenceAlgorithms import InferenceAlgorithms as InfAlgo
from agents.learning import Optimizers


class TemporalSlice:
    """
    A class representing a temporal slice that can contain several states,
    actions and observations.
    """

    def __init__(
            self, fg, n_actions, action_name, obs_prior_pref, obs_likelihood,
            states_prior, states_transition, states_parents, obs_parents
    ):
        """
        Create a temporal slice.
        :param fg: the factor graph of the temporal slice.
        :param n_actions: the number of actions.
        :param action_name: the name of the action random variable.
        :param obs_prior_pref: the prior preferences over observations.
        :param obs_likelihood: the likelihood mapping of the observations.
        :param states_prior: the prior beliefs over hidden states.
        :param states_transition: the transition mappings of hidden states.
        :param states_parents: the parents of each state.
        :param obs_parents: the parents of each observation.
        """
        self.n_actions = n_actions
        self.action_name = action_name
        self.fg = fg
        self.obs_prior_pref = obs_prior_pref
        self.obs_likelihood = obs_likelihood
        self.obs_parents = obs_parents
        self.initial_states_prior = {k: v.clone() for k, v in states_prior.items()}
        self.states_prior = states_prior
        self.states_transition = states_transition
        self.states_parents = states_parents
        self.states_posterior = {k: torch.ones_like(v) for k, v in states_prior.items()}
        self.obs_posterior = {k: torch.ones_like(v) for k, v in obs_likelihood.items()}
        self.action = -1
        self.cost = 0
        self.visits = 1
        self.parent = None
        self.children = []
        self.encoder = None
        self.optimizer = None if self.encoder is None else Optimizers.get_adam([self.encoder], 0.001)
        self.to_i_step = {
            InfAlgo.BELIEF_PROPAGATION: self.i_step_bp,
            InfAlgo.LOOPY_BELIEF_PROPAGATION: self.i_step_lbp,
            InfAlgo.BACKPROPAGATION: self.i_step_backpropagation,
        }

    def reset(self):
        """
        Reset the temporal slice attributes to their initial values.
        :return: nothing.
        """
        self.fg.reset_messages()
        self.states_prior = {k: v.clone() for k, v in self.initial_states_prior.items()}
        self.cost = 0
        self.visits = 1
        self.parent = None
        self.children = []

    def uct(self, exp_const):
        """
        Compute the UCT criterion.
        :param exp_const: the exploration constant.
        :return: nothing.
        """
        return - self.cost / self.visits + \
            exp_const * math.sqrt(math.log(self.parent.visits) / self.visits)

    def use_posteriors_as_empirical_priors(self):
        """
        Set the states priors equal to the states posteriors.
        """
        for state, params in self.states_posterior.items():
            self.fg[state].params = params

    def i_step(self, obs, inf_type=InfAlgo.LOOPY_BELIEF_PROPAGATION):
        """
        Perform the I-step, i.e., compute the posterior beliefs using the inference algorithm requested by the user
        :param obs: the observations made by the agent
        :param inf_type: the type of inference to use
        :return: nothing
        """
        try:
            self.to_i_step[inf_type](obs)
        except RuntimeError:
            self.fg.reset_messages()
            if inf_type != InfAlgo.LOOPY_BELIEF_PROPAGATION:
                print(
                    "[ERROR] The requested inference algorithm failed to compute the posterior distributions. As a "
                    "last resort, loopy belief propagation will be run."
                )
                self.to_i_step[InfAlgo.LOOPY_BELIEF_PROPAGATION](obs)
            else:
                print("[ERROR] The requested inference algorithm failed to compute the posterior distributions.")

    def i_step_bp(self, obs):
        """
        Perform the I-step, i.e., compute the posterior beliefs using beliefs propagation
        :param obs: the observations made by the agent
        :return: nothing
        """
        # Set the evidence of each observation.
        for name, evidence in obs.items():
            self.fg.set_evidence(name, evidence)

        # Create a queue containing all the leaf nodes.
        q = queue.Queue()
        for node in self.fg.leaf_nodes():
            q.put(node)

        # Perform the belief propagation algorithm.
        while not q.empty():
            node = q.get()
            for t_node in self.get_target_nodes(node):
                t_node.in_messages[node.name] = node.compute_message(t_node.name)
                if self.count_none_messages(t_node) <= 1:
                    q.put(t_node)

        # Compute the posterior over all latent states.
        self.compute_posterior_distributions()

    def i_step_lbp(self, obs):
        """
        Perform the I-step, i.e., compute the posterior beliefs using loopy beliefs propagation
        :param obs: the observations made by the agent
        :return: nothing.
        """
        # Set the evidence of each observation.
        for name, evidence in obs.items():
            self.fg.set_evidence(name, evidence)

        # Perform the loopy belief propagation algorithm.
        nodes = list(self.fg.factor_nodes()) + list(self.fg.variable_nodes())
        max_error = 1
        while max_error >= 1:
            max_error = 0
            for node in nodes:
                for t_node in node.neighbours:
                    msg = node.compute_message(t_node, use_default_val=True)
                    t_node_msg = self.fg[t_node].in_messages[node.name]
                    max_error = max(1 if t_node_msg is None else np.abs(t_node_msg - msg).max(), max_error)
                    if isinstance(msg, np.ndarray):
                        msg = torch.from_numpy(msg)
                    if msg.isnan().any():
                        exit(42)
                    t_node = self.fg[t_node]
                    t_node.in_messages[node.name] = msg

        # Compute the posterior over all latent states.
        self.compute_posterior_distributions()

    def i_step_backpropagation(self, obs, learn=True):
        """
        Perform the I-step, i.e., compute the posterior beliefs using an encoder network trained using backpropagation
        :param obs: the observations made by the agent
        :param learn: whether to learn the encoder weights
        :return: nothing.
        """
        # Pre-process images
        init_obs = copy.deepcopy(obs)
        obs = Image.fromarray(obs.astype(np.uint8))
        obs = obs.resize((20, 20), Image.ANTIALIAS)
        obs = torch.from_numpy(np.array(obs)).unsqueeze(dim=0).permute(0, 3, 1, 2).type(torch.float32)

        # Create encoder if it does not exist
        if self.encoder is None:
            n_outputs = sum([v.shape[0] for v in self.states_posterior.values()])
            self.encoder = self.create_encoder(n_outputs)

        # Compute the variational posteriors
        shift = 0
        posteriors = self.encoder(obs)
        for k, posterior in self.states_posterior.items():
            size = posterior.shape[0]
            self.states_posterior[k] = posteriors[0, shift:shift + size]
            shift += size

        # Check whether learning must be performed
        if not learn:
            return

        # Compute the complexity.
        kl_div = sum([
            kl_div_categorical(posterior, prior)
            for prior, posterior in zip(self.states_prior.values(), self.states_posterior.values())
        ])

        # Compute the accuracy.
        accuracies = {}
        for obs_name in self.obs_posterior.keys():
            accuracies[obs_name] = self.forward_prediction(
                self.obs_likelihood[obs_name], 0, self.obs_parents[obs_name], self.states_posterior
            )
        print(obs.shape)
        print(init_obs.shape)
        print(init_obs.max())
        print(init_obs.min())
        print()
        accuracy = None  # TODO get observation probability and sum them

        # Compute the variational free energy
        vfe = kl_div + accuracy

        # Perform backpropagation
        self.optimizer.zero_grad()
        vfe.backward()
        self.optimizer.step()

    def compute_posterior_distributions(self):
        """
        Compute the (marginal) posterior distributions from pre-computed messages
        """
        # Compute the posterior over all latent states.
        for node in self.fg.state_nodes():
            self.states_posterior[node.name] = torch.ones_like(self.states_posterior[node.name])
            for _, message in node.in_messages.items():
                if message is None:
                    raise RuntimeError(
                        "Could not perform belief propagation: one of the message is None, which suggest that the "
                        "generative model is not a poly-tree."
                    )
                self.states_posterior[node.name] *= message
            normalisation = self.states_posterior[node.name].sum()
            if normalisation == 0:
                self.states_posterior[node.name] += 1
            self.states_posterior[node.name] /= self.states_posterior[node.name].sum()

    def get_target_nodes(self, node):
        """
        Get the neighbours of the input node that still requires a message
        from the input node.
        :param node: the input node whose neighbours must be returned.
        :return: the neighbours that still requires a message from the input node.
        """
        t_nodes = []
        for neighbour in node.in_messages.keys():
            if not self.received_message(node.name, neighbour) and self.can_compute_message(node.name, neighbour):
                t_nodes.append(self.fg[neighbour])
        return t_nodes

    def received_message(self, from_node, to_node):
        """
        Check if a message has been sent from a node to another.
        :param from_node: the node from which the message originates.
        :param to_node: the node that receives the message.
        :return: True if a message has been received by "to_node" from "from_node", False otherwise.
        """
        return self.fg[to_node].in_messages[from_node] is not None

    def can_compute_message(self, to_node, from_node):
        """
        Check if a message can be computed from one node to another.
        :param from_node: the node from which the message originates.
        :param to_node: the node that receives the message.
        :return: True if the message from "from_node" to "to_node" can be computed, False otherwise.
        """
        for neighbour, message in self.fg[to_node].in_messages.items():
            if neighbour != from_node and message is None:
                return False
        return True

    @staticmethod
    def count_none_messages(node):
        """
        Count the number of messages not received by the input node yet.
        :param node: the input node.
        :return: the number of messages not received yet.
        """
        return sum(map(lambda value: value is None, node.in_messages.values()))

    def p_step(self, action):
        """
        Perform the P-step, i.e., compute the posterior beliefs using forward predictions.
        :param action: the action taken by the agent.
        :return: nothing.
        """
        # Create a new temporal slice.
        next_ts = TemporalSlice(
            self.fg, self.n_actions, self.action_name, self.obs_prior_pref,
            self.obs_likelihood, self.states_prior, self.states_transition,
            self.states_parents, self.obs_parents
        )
        next_ts.action = action
        next_ts.parent = self
        self.children.append(next_ts)

        # Create a one hot encoding of the action.
        action = torch.squeeze(one_hot(torch.tensor([action]), self.n_actions))

        # Compute the posterior over the future states.
        for state_name in self.states_posterior.keys():
            next_ts.states_posterior[state_name] = self.forward_prediction(
                self.states_transition[state_name], action,
                self.states_parents[state_name], self.states_posterior
            )

        # Compute the posterior over the future observations.
        for obs_name in self.obs_posterior.keys():
            next_ts.obs_posterior[obs_name] = self.forward_prediction(
                self.obs_likelihood[obs_name], action,
                self.obs_parents[obs_name], next_ts.states_posterior
            )

        return next_ts

    def forward_prediction(self, params, action, parents, posteriors):
        """
        Compute the forward prediction of the posterior over a random variable assuming
        a particular mapping and action.
        :param params: the parameters of the mapping.
        :param action: the action taken.
        :param parents: the parents of the random variable  named 'dest_name'.
        :param posteriors: the posterior over the parents.
        :return: the predictive posterior of the random variable named 'dest_name'.
        """
        for parent in reversed(parents):
            posterior = action if parent == self.action_name else posteriors[parent]
            i = parents.index(parent)
            params = Operators.average(params, posterior, [i + 1])
        return params

    def efe(self, n_samples=1):
        """
        Compute the expected free energy of the temporal slice.
        :param n_samples: the number of samples to use to compute the risk, -1 if an analytical solution must be used
        :return: the expected free energy.
        """
        return sum(self.compute_risk_terms(n_samples)) + sum(self.compute_ambiguity_terms(n_samples))

    def compute_risk_terms(self, n_samples=-1):
        """
        Compute all the risk terms of the expected free energy.
        :param n_samples: the number of samples to use to compute the risk, -1 if an analytical solution must be used
        :return: the sum of all risk terms.
        """
        risk_terms = []
        processed_modalities = []

        # For each modality.
        for obs_name, (rv_names, prior_pref) in self.obs_prior_pref.items():

            # Check if the risk term of this modality has already been computed.
            if obs_name in processed_modalities:
                continue

            # Compute the posterior over the subset of observations.
            subset_posterior = None
            for rv_name in rv_names:
                if subset_posterior is None:
                    subset_posterior = self.obs_posterior[rv_name]
                else:
                    rv_posterior = self.obs_posterior[rv_name]
                    subset_posterior = torch.outer(subset_posterior, rv_posterior)
                    subset_posterior = subset_posterior.view(-1)

            # Compute the risk term of the expected free energy.
            if n_samples == -1:
                # Using an analytical solution
                risk = subset_posterior * (subset_posterior.log() - prior_pref.log().view(-1))
                risk = risk.sum()
            else:
                # Using sampling
                risk = []
                for _ in range(n_samples):
                    i = random.choices(range(len(subset_posterior)), subset_posterior)
                    risk.append(subset_posterior.log()[i] - prior_pref.log()[i])
                risk = sum(risk) / len(risk)

            # Save risk term.
            risk_terms.append(risk.item())

            # Add the random variable of the subset to the list of processed modalities.
            processed_modalities += rv_names

        return risk_terms

    def compute_ambiguity_terms(self, n_samples=-1):
        """
        Compute the all the ambiguity terms of the expected free energy.
        :param n_samples: the number of samples to use to compute the risk, -1 if an analytical solution must be used
        :return: the sum of all ambiguity terms.
        """
        ambiguity_terms = []

        # For each modality.
        for obs_name in self.obs_likelihood.keys():
            # Compute the ambiguity.
            ambiguity = - self.obs_likelihood[obs_name].log()
            if n_samples == -1:
                # Using an analytical solution
                ambiguity = Operators.average(
                    ambiguity, self.obs_likelihood[obs_name],
                    [i for i in range(ambiguity.dim())],
                    [i for i in range(1, ambiguity.dim())]
                )
                for parent in reversed(self.obs_parents[obs_name]):
                    i = self.obs_parents[obs_name].index(parent)
                    ambiguity = Operators.average(ambiguity, self.states_posterior[parent], [i])
            else:
                # Using sampling
                ambiguities = []
                for _ in range(n_samples):
                    a = ambiguity
                    log_a = self.obs_likelihood[obs_name]
                    length = len(ambiguity.shape)
                    for j, max_i in enumerate(reversed(ambiguity.shape)):
                        j_tmp = length - j - 1
                        i = random.choices(
                            range(0, max_i),
                            log_a if j_tmp == 0 else self.states_posterior[self.obs_parents[obs_name][j_tmp - 1]]
                        )
                        a = torch.index_select(a, j_tmp, torch.tensor(i))
                        log_a = torch.index_select(log_a, j_tmp, torch.tensor(i))
                    ambiguities.append(a)
                ambiguity = sum(ambiguities) / len(ambiguities)

            # Save the ambiguity term.
            ambiguity_terms.append(ambiguity.item())

        return ambiguity_terms

    @staticmethod
    def create_encoder(n_outputs):
        """
        Create the encoder network
        :param n_outputs: the number of output neurons
        :return: the encoder network
        """
        return nn.Sequential(
            nn.Conv2d(3, 32, (3, 3), stride=(2, 2), padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, (3, 3), stride=(2, 2), padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 64, (3, 3), stride=(2, 2), padding=1),
            nn.ReLU(),
            nn.Flatten(start_dim=1),
            nn.Linear(576, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, n_outputs),
            nn.Softmax(),
        )
