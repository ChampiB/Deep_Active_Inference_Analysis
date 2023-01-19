import torch
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure

figure(figsize=(9, 6), dpi=80)


def draw(data, labels, efe_cost=True):
    n = int((data.shape[1] - 1) / 2)  # number of different sampling sizes and critic networks
    data = data[data[:, 0].argsort()]  # sort the data according to the analytical expected free energy
    analytic_color = ['black']
    sampling_colors = ['limegreen', 'greenyellow', 'orange', 'red', 'darkred']
    critic_colors = ['indigo', 'purple', 'darkviolet', 'crimson', 'hotpink', 'pink']
    cost = 'expected free energy' if efe_cost is True else 'reward'

    for draw_type in range(3):
        if draw_type == 0:
            indices = [0] + [i for i in range(n + 1, data.shape[1])]
            xs = data[:, indices]
            colors_list = analytic_color + sampling_colors
            curves_label = [labels[0]] + labels[n + 1:]
            plt.title(f"Impact of sampling on {cost} estimation")
        elif draw_type == 1:
            xs = data[:, :n + 1]
            colors_list = analytic_color + critic_colors[:n]
            curves_label = labels[:n + 1]
            plt.title(f"Impact of critic on {cost} estimation")
        elif draw_type == 2:
            xs = data
            colors_list = analytic_color + critic_colors[:n] + sampling_colors[:n]
            curves_label = labels
            plt.title(f"Estimation of the {cost}")
        else:
            raise RuntimeError("Invalid drawing type.")

        # Plotting all curves simultaneously
        x_axis = [x for x in range(xs.shape[0])]
        for index, y in enumerate(range(xs.shape[1])):
            plt.plot(x_axis, xs[:, y], color=colors_list[index], label=curves_label[index])

        # Naming the x-axis, y-axis and the whole graph
        plt.xlabel(f"Increasingly big {cost}")
        plt.ylabel(f"Predicted {cost}")

        # Shrink current axis by 20%
        box = plt.gca().get_position()
        plt.gca().set_position([box.x0, box.y0, box.width * 0.8, box.height])

        # Adding legend, which helps us recognize the curve according to it's color
        plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
        plt.savefig(f"figs/{'efe' if efe_cost is True else 'reward'}_drawing_type_{draw_type}.png")
        plt.show(block=False)
        plt.clf()


if __name__ == '__main__':
    device = torch.device("cuda:0")

    print("Loading CSV files...")
    efe_data = pd.read_csv("data/efe_data.csv")
    reward_data = pd.read_csv("data/reward_data.csv")

    print("Converting to Tensor...")
    efe_values = torch.Tensor(efe_data.values).numpy()
    reward_values = torch.Tensor(reward_data.values).numpy()

    print("Extracting labels...")
    efe_labels = efe_data.keys().to_list()
    reward_labels = reward_data.keys().to_list()

    print("Displaying graphs...")
    draw(data=efe_values, labels=efe_labels, efe_cost=True)
    draw(data=reward_values, labels=reward_labels, efe_cost=False)
