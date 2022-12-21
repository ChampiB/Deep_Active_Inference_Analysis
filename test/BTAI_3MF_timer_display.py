import matplotlib.pyplot as plt
import numpy as np


def draw_grid(data):
    # Plotting execution time
    xs = data[:, 0]
    ys = data[:, 1]
    plt.plot(xs, np.log(xs), color='orange', label="log(x)")
    plt.plot(xs, xs, color='lightblue', label="x")
    plt.plot(xs, xs ** 2, color='green', label="x²")
    plt.plot(xs, 0.65 * xs ** 2, color='lightgray', label="0.65 x²")
    plt.plot(xs, ys, color='red', label="BTAI_3MF execution time")

    # Naming the x-axis, y-axis and the whole graph
    plt.ylabel("BTAI_3MF execution time (seconds)")
    plt.xlabel("MiniSprites size")

    # Adding legend, which helps us recognize the curve according to it's color
    plt.legend()

    # Save and display yhe figure
    plt.savefig("figs/btai_3mf_timer.png")
    plt.show()


if __name__ == '__main__':
    data = np.asarray([
        [2, 2.0459959506988525],
        [3, 4.33856987953186],
        [4, 8.234893083572388],
        [5, 12.509858846664429],
        [6, 21.653692960739136],
        [7, 30.65618062019348],
        [8, 39.42964196205139],
        [9, 50.583593130111694],
        [10, 60.75343036651611],
        [11, 74.35180401802063],
        [12, 89.71236371994019],
        [13, 114.4069676399231],
        [14, 142.14582228660583],
        [15, 156.05535244941711],
        [16, 163.8569896221161],
        [17, 181.85322332382202],
        [18, 204.8925359249115],
        [19, 219.00606060028076],
        [20, 259.1389422416687]
    ])

    draw_grid(data)
