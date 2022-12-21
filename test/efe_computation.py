from torch import nn
from agents.inference.TemporalSliceBuilder import TemporalSliceBuilder
from agents.learning import Optimizers
from agents.planning.MCTS import MCTS
import torch
from environments.impl.MiniSpritesEnvironment import MiniSpritesEnvironment


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


def create_temporal_slide(env, n_actions):
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


def run(ts, max_number_of_points, verbose=True, training=False):
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
                state = torch.cat(
                    [node.states_posterior["S_x"], node.states_posterior["S_y"], node.states_posterior["S_color"]],
                    dim=0
                )
                critic_efe = critic(state)
                if verbose:
                    print(
                        #  f"{node.efe(1)},{node.efe(10)},{node.efe(100)},{node.efe(1000)},{node.efe(-1)}," +
                        f"{critic_efe.item()}"
                    )
                if training:
                    efe_target = torch.tensor([node.efe(-1)])
                    loss = nn.SmoothL1Loss()(critic_efe, efe_target)
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()
                if j >= max_number_of_points:
                    return
            mcts.propagation(e_nodes)
        action = max(ts.children, key=lambda x: x.visits).action
        ts = next(filter(lambda x: x.action == action, ts.children))
        ts.use_posteriors_as_empirical_priors()
        obs, _, _, _ = env.step(action)


if __name__ == '__main__':
    width = "5"
    height = "5"
    env = MiniSpritesEnvironment({"width": width, "height": height, "max_trial_length": "50"})
    n_actions = env.action_space.n
    temporal_slide = create_temporal_slide(env, n_actions)
    mcts = MCTS(2.4, n_samples=150)
    n_neurons = 100
    critic = nn.Sequential(
        nn.Linear(int(width) + int(height) + 2, n_neurons),
        nn.ReLU(),
        nn.Linear(n_neurons, n_neurons),
        nn.ReLU(),
        nn.Linear(n_neurons, n_neurons),
        nn.ReLU(),
        nn.Linear(n_neurons, 1),
    )
    optimizer = Optimizers.get_adam([critic], 0.0001)

    run(temporal_slide, max_number_of_points=100, verbose=False, training=True)
    print("EFE_1_sample, EFE_10_samples, EFE_100_samples, EFE_1000_samples, EFE_analytic, EFE_critic")
    run(temporal_slide, max_number_of_points=100)
