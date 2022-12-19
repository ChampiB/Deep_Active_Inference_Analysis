from mpl_toolkits.axes_grid1.axes_divider import make_axes_locatable
import matplotlib.pyplot as plt
from matplotlib import colors
import numpy as np
import math


def draw_grid(data):
    colors_list = ['deepskyblue', 'skyblue', 'paleturquoise', 'palegreen', 'chartreuse', 'greenyellow', 'yellow', 'orange', 'darkorange', 'red']
    n_colors = 10
    data = data - np.min(data)
    data = data / np.max(data)
    step = 10 ** 15 / n_colors
    bounds = [np.min(data) + math.log(step * i + 0.01) / math.log(step * n_colors + 0.001) for i in range(n_colors)]

    # create discrete colormap
    cmap = colors.ListedColormap(colors_list)
    norm = colors.BoundaryNorm(bounds, cmap.N)

    fig, ax = plt.subplots()
    img = ax.imshow(data, cmap=cmap, norm=norm)

    # draw gridlines
    ax.grid(axis='both', linestyle='-', color='k', linewidth=2)
    ax.set_xticks(np.arange(-.5, 10, 1))
    ax.set_yticks(np.arange(-.5, 10, 1))
    ax.invert_yaxis()
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_xticks(np.arange(0, 10, 1), minor=True)
    ax.set_yticks(np.arange(0, 10, 1), minor=True)
    ax.set_xticklabels([y / 10 for y in range(1, 11)], minor=True)
    ax.set_yticklabels([y for y in range(0, 10)], minor=True)

    for tick in ax.xaxis.get_major_ticks():
        tick.tick1line.set_visible(False)
        tick.tick2line.set_visible(False)
        tick.label1.set_visible(False)
        tick.label2.set_visible(False)

    for tick in ax.yaxis.get_major_ticks():
        tick.tick1line.set_visible(False)
        tick.tick2line.set_visible(False)
        tick.label1.set_visible(False)
        tick.label2.set_visible(False)

    plt.ylabel("Mean of P(S)")
    plt.xlabel("Variance of P(S)")

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)
    fig.colorbar(img, cax=cax)
    plt.savefig("epistemic_value.png")
    plt.show()


if __name__ == '__main__':
    data = np.zeros([10, 10])
    mu_q = 0
    sigma_q = 1
    for mu_p in range(0, 10):
        for std_index in range(1, 11):
            sigma_p = float(std_index) / 10
            data[mu_p][std_index - 1] = \
                0.5 * math.log(2 * math.pi * sigma_q) \
                + 0.5 \
                - math.log(math.sqrt(2 * math.pi) * sigma_p) \
                - (sigma_q ** 2 + mu_q ** 2 - 2 * mu_q * mu_p + mu_p ** 2) / (2 * (sigma_p ** 2))

    draw_grid(data)
