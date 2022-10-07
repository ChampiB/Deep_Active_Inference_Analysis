from torch.distributions.multivariate_normal import MultivariateNormal
from torch import zeros, eye
import torch
from hosts.HostInterface import HostInterface


def re_parameterize(mean, log_var):
    """
    Perform the re-parameterization trick
    :param mean: the mean of the Gaussian
    :param log_var: the log of the variance of the Gaussian
    :return: a sample from the Gaussian on which back-propagation can be performed
    """
    nb_states = mean.shape[1]
    device = HostInterface.get_device()
    epsilon = MultivariateNormal(zeros(nb_states), eye(nb_states)).sample([mean.shape[0]]).to(device)
    return epsilon * torch.exp(0.5 * log_var) + mean


def kl_div_gaussian(mean_hat, log_var_hat, mean, log_var, sum_dims=None):
    """
    Compute the KL-divergence between two Gaussian distributions
    :param mean: the mean of the first Gaussian distribution
    :param log_var: the logarithm of variance of the first Gaussian distribution
    :param mean_hat: the mean of the second Gaussian distribution
    :param log_var_hat: the logarithm of variance of the second Gaussian distribution
    :param sum_dims: the dimensions along which to sum over before to return, by default all of them
    :return: the KL-divergence between the two Gaussian distributions
    """
    var = torch.clamp(log_var, max=10).exp()  # Clamp to avoid overflow of exponential
    var_hat = torch.clamp(log_var_hat, max=10).exp()  # Clamp to avoid overflow of exponential
    kl_div = log_var - log_var_hat + var_hat / var + (mean_hat - mean) ** 2 / var

    if sum_dims is None:
        return 0.5 * kl_div.sum(dim=1).mean()
    else:
        return 0.5 * kl_div.sum(dim=sum_dims)


def compute_info_gain(g_value, mean_hat, log_var_hat, mean, log_var):
    """
    Compute the efe.
    :param g_value: the definition of the efe to use, i.e., reward, efe_0, efe_1,
        efe_2, efe_3, befe_0, befe_1, befe_2, and befe_3.
    :param mean_hat: the mean from the encoder.
    :param log_var_hat: the log variance from the encoder.
    :param mean: the mean from the transition.
    :param log_var: the log variance from the transition.
    :return: the efe.
    """
    efe = torch.zeros([1]).to(HostInterface.get_device())
    if g_value == "Expected Free Energy":
        efe = kl_div_gaussian(mean, log_var, mean_hat, log_var_hat)
    return efe


def log_bernoulli_with_logits(obs, alpha):
    """
    Compute the log probability of the observation (obs), given the logits (alpha), assuming
    a bernoulli distribution, c.f.
    https://www.tensorflow.org/api_docs/python/tf/nn/sigmoid_cross_entropy_with_logits
    :param obs: the observation
    :param alpha: the logits
    :return: the log probability of the observation
    """
    out = torch.exp(alpha)
    one = torch.ones_like(out)
    out = alpha * obs - torch.log(one + out)
    return out.sum(dim=(1, 2, 3)).mean()
