from torch import nn
import copy
from torch.distributions import Categorical
from agents.inference.TemporalSliceBuilder import TemporalSliceBuilder
from agents.learning import Optimizers
from agents.planning.MCTS import MCTS
import torch
from environments.impl.MiniSpritesEnvironment import MiniSpritesEnvironment


#
# BTAI_3MF agent definition
#
def a_matrix(env, noise=0.01):
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


def b_matrix(env, n_actions, noise=0.01):
    transitions = {}
    # Generate the transition matrix of S_color for which action has no effect.
    transition = torch.full([env.s_sizes[2], env.s_sizes[2]], noise / (env.s_sizes[2] - 1))
    for j in range(env.s_sizes[2]):
        transition[j][j] = 1 - noise
    transitions[env.state_names[2]] = transition
    # Generate transitions for which action has an effect.
    for i in range(2):
        transition = torch.full([env.s_sizes[i], env.s_sizes[i], n_actions], noise / (env.s_sizes[i] - 1))
        for j in range(env.s_sizes[i]):
            cur_state = torch.zeros([len(env.s_sizes)])
            cur_state[i] = j
            for k in range(n_actions):
                env.x, env.y, env.reward_on_the_right = cur_state[0], cur_state[1], bool(cur_state[2])
                env.step(k)
                dest_state = torch.tensor([env.x, env.y, int(env.reward_on_the_right)])
                dest_id = int(dest_state[i].item())
                transition[dest_id][j][k] = 1 - noise
        transitions[env.state_names[i]] = transition
    return transitions


def c_matrix(noise=0.01):
    preferences = {"O_bottom_left": torch.full([3], noise / 3), "O_bottom_right": torch.full([3], noise / 3)}
    # Create preferences for the bottom right and left corners.
    preferences["O_bottom_left"][0] = 1 - noise
    preferences["O_bottom_right"][1] = 1 - noise
    return preferences


def d_matrix(env, uniform=False, noise=0.01):
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


def create_temporal_slice(env, n_actions):
    env = env.unwrapped
    a = a_matrix(env)
    b = b_matrix(env, n_actions)
    c = c_matrix()
    d = d_matrix(env, uniform=True)
    ts_builder = TemporalSliceBuilder("A_0", n_actions) \
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


def pre_process(obs):
    res = {}
    for y in range(obs.shape[0]):
        for x in range(obs.shape[1]):
            res[f"O_{x}_{y}"] = obs[y][x] / 255
            if obs[y][x].max() == 0:
                res[f"O_{x}_{y}"][2] = 1
    return res


#
# The code collecting and displaying the data
#
def collect_dataset(ts, n_examples, sampling=False, efe_cost=True):
    dataset = {"x": [], "y": []}
    j = 0
    obs = env.reset()
    while True:
        ts.reset()
        obs = pre_process(obs)
        ts.i_step(obs)
        for i in range(0, 50):
            node = mcts.select_node(ts)
            e_nodes = mcts.expansion(node)
            mcts.evaluation(e_nodes)
            for node in e_nodes:
                j += 1
                states = [node.states_posterior[key] for key in ["S_x", "S_y", "S_color"]]
                if sampling is True:
                    for index, probs in enumerate(states):
                        state = Categorical(probs=probs).sample()
                        states[index] = torch.zeros(probs.shape[0])
                        states[index][state] = 1
                states = torch.cat(states, dim=0)
                dataset["x"].append(states)
                if efe_cost is True:
                    dataset["y"].append(torch.tensor(node.efe(-1)))
                else:
                    dataset["y"].append(torch.tensor(node.reward(-1)))
                if j >= n_examples:
                    return dataset
            mcts.propagation(e_nodes)
        action = max(ts.children, key=lambda x: x.visits).action
        ts = next(filter(lambda x: x.action == action, ts.children))
        ts.use_posteriors_as_empirical_priors()
        obs, _, _, _ = env.step(action)


def train(critic_net, dataset, n_epochs=1):
    optimizer = Optimizers.get_adam([critic_net], 0.0001)
    i = 0
    while i != n_epochs:
        for state, efe_target in zip(dataset["x"], dataset["y"]):
            critic_efe = critic_net(state)
            loss = nn.SmoothL1Loss()(critic_efe, efe_target)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        i += 1


def display_cost_prediction(ts, n_points, critic_networks, max_n_samples, efe_cost):
    # Display the csv header
    n = 0
    while 10 ** n != max_n_samples:
        n += 1
    cost_type = "efe" if efe_cost is True else "reward"
    print(
        f"{cost_type}_analytic,"
        f"{','.join([f'{cost_type}_critic_{10 ** i}' for i in range(n)])},"
        f"{','.join([f'{cost_type}_sampling_{10 ** i}' for i in range(n)])}"
    )

    # Display the csv rows
    j = 0
    obs = env.reset()
    while True:
        ts.reset()
        obs = pre_process(obs)
        ts.i_step(obs)
        for i in range(0, 150):
            node = mcts.select_node(ts)
            e_nodes = mcts.expansion(node)
            mcts.evaluation(e_nodes)
            for node in e_nodes:
                j += 1
                # Get current state as vector
                state = torch.cat(
                    [node.states_posterior["S_x"], node.states_posterior["S_y"], node.states_posterior["S_color"]],
                    dim=0
                )

                # Compute cost analytically
                s = f"{node.efe(-1)}" if efe_cost is True else f"{node.reward(-1)}"

                # Compute cost using each critic
                for critic_net in critic_networks:
                    s += f",{critic_net(state).item()}"

                # Compute cost using sampling
                n_samples = 1
                while n_samples != max_n_samples:
                    s += f",{node.efe(n_samples)}" if efe_cost is True else f",{node.reward(max_n_samples)}"
                    n_samples *= 10

                # Display all costs
                print(s)

                # Check for terminal condition
                if j >= n_points:
                    return
            mcts.propagation(e_nodes)
        action = max(ts.children, key=lambda x: x.visits).action
        ts = next(filter(lambda x: x.action == action, ts.children))
        ts.use_posteriors_as_empirical_priors()
        obs, _, _, _ = env.step(action)


#
# Main script instantiating the environment and agent to collect the data
#
if __name__ == '__main__':
    # Define the type of cost to use
    efe_cost = False

    # Create the environment
    width = "5"
    height = "5"
    env = MiniSpritesEnvironment({"width": width, "height": height, "max_trial_length": "50"})
    n_actions = env.action_space.n

    # Create the agent related structures, i.e., temporal slice, mcts algorithm, critic and optimiser
    temporal_slice = create_temporal_slice(env, n_actions)
    mcts = MCTS(2.4)
    n_neurons = 100
    initial_critic = nn.Sequential(
        nn.Linear(int(width) + int(height) + 2, n_neurons),
        nn.ReLU(),
        nn.Linear(n_neurons, n_neurons),
        nn.ReLU(),
        nn.Linear(n_neurons, n_neurons),
        nn.ReLU(),
        nn.Linear(n_neurons, 1),
    )
    print("Initialisation: OK.")

    # Collect the dataset and train the critic network on it
    ds = collect_dataset(temporal_slice, n_examples=1000, sampling=True, efe_cost=efe_cost)
    print("Data collection: OK.")

    critics = []
    n_examples = 1
    max_n_examples = 10000
    while n_examples != max_n_examples:
        print(f"Training {n_examples}_critic: IN PROGRESS...")
        n_epochs = int(100000 / n_examples)
        critic = copy.deepcopy(initial_critic)
        train(critic, {"x": ds["x"][:n_examples], "y": ds["y"][:n_examples]}, n_epochs=n_epochs)
        critics.append(critic)
        n_examples *= 10
    print("Training: OK.")

    # Display expected free energy prediction
    display_cost_prediction(temporal_slice, 100, critics, max_n_examples, efe_cost)
    print("Display: OK.")
