import matplotlib.pyplot as plt
import pandas
import numpy as np
import torch


def display_debug(posteriors, variational_posterior):
    figure, axes = plt.subplots(nrows=4, ncols=5)  # len(posteriors)
    i = 0
    for row in axes:
        df = pandas.DataFrame(posteriors[i])
        j = 0
        for col in row:
            if j < 2:
                y = df[j % 2] / df[j % 2].sum()
                col.bar([f"p(s1|o{j+1})={round(float(y[0]), 2)}", f"p(s2|o{j+1})={round(float(y[1]), 2)}"], y)
            elif j < 4:
                y = df[j % 2] / df[j % 2].sum()
                y = np.log(y)
                col.bar([
                    f"ln p(s1|o{j%2+1})={round(float(y[0]), 2)}",
                    f"ln p(s2|o{j%2+1})={round(float(y[1]), 2)}"
                ], y)
            elif j < 6:
                y = variational_posterior.log()
                col.bar([
                    f"q(s1)={round(float(y[0]), 2)}",
                    f"q(s2)={round(float(y[1]), 2)}"
                ], y)
            j += 1
        i += 1
    figure.show()


def compute_posteriors(likelihoods, state_prior):
    posteriors = []
    for i in range(likelihoods.shape[0]):
        likelihood = likelihoods[i]
        posterior = torch.zeros([2, 2])
        for j in range(posterior.shape[0]):
            for k in range(posterior.shape[1]):
                posterior[j][k] = likelihood[k][j] * state_prior[j]
        posterior *= 1 / posterior.sum(dim=0)
        posteriors.append(posterior)
    return posteriors


def compute_epistemic_values(variational_posterior, posteriors, likelihoods):
    epistemic_values = []
    for i in range(likelihoods.shape[0]):
        # Compute the distribution w.r.t which the expectation is taken
        likelihood = likelihoods[i]
        joint_distribution = torch.zeros([2, 2])
        for j in range(likelihood.shape[0]):
            for k in range(likelihood.shape[1]):
                joint_distribution[j][k] = likelihood[j][k] * variational_posterior[k]

        # Compute the expectation content
        log_posterior = posteriors[i].log()
        log_variational_posterior = variational_posterior.log()
        inner_value = torch.zeros([2, 2])
        for j in range(likelihood.shape[0]):
            for k in range(likelihood.shape[1]):
                inner_value[j][k] = log_posterior[k][j] - log_variational_posterior[k]

        # Compute the epistemic value
        epistemic_value = (inner_value * joint_distribution).sum()
        epistemic_values.append(epistemic_value)

    return epistemic_values


def display_epistemic_values(epistemic_values):
    plt.figure()

    # Plotting execution time
    xs = [0.5 + 0.05 * i for i in range(len(epistemic_values))]
    ys = epistemic_values
    plt.plot(xs, ys, color='lightblue', label="x")

    # Naming the x-axis, y-axis and the whole graph
    plt.ylabel("Epistemic value")
    plt.xlabel("x")

    # Save and display the figure
    plt.show()
    print(epistemic_values)


if __name__ == '__main__':
    print("Initialisation: In progress...")
    Q = torch.tensor([0.8, 0.2])
    D = torch.tensor([0.8, 0.2])
    shift = 0.05
    As = torch.tensor([
        [
            [0.5 + shift * x, 0.5],
            [0.5 - shift * x, 0.5]
        ] for x in range(10)
    ])
    print("Initialisation: OK.")

    print("Posterior computation: In progress...")
    Ps = compute_posteriors(As, D)
    print("Posterior computation: Ok.")

    print("Epistemic value computation: In progress...")
    EVs = compute_epistemic_values(Q, Ps, As)
    print("Epistemic value computation: OK.")

    print("Epistemic value display: In progress...")
    display_epistemic_values(EVs)
    print("Epistemic value display: OK.")
