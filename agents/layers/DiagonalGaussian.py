from torch import nn


class DiagonalGaussian(nn.Module):
    """
    Class implementing a network that maps a vector of size n into two vectors representing the mean
    and variance of a Gaussian with diagonal covariance matrix
    """

    def __init__(self, input_size, nb_components):
        """
        Constructor
        :param input_size: size of the vector send as input of the layer
        :param nb_components: the number of components of the diagonal Gaussian
        """
        super().__init__()
        self.__mean = nn.Sequential(
            nn.Linear(input_size, nb_components)
        )
        self.__log_var = nn.Sequential(
            nn.Linear(input_size, nb_components),
        )

    def forward(self, x):
        """
        Compute the mean and the variance of the diagonal Gaussian (DG)
        :param x: the input vector
        :return: the mean and the log of the variance of the DG
        """
        return self.__mean(x), self.__log_var(x)
