from torch import nn


class LinearRelu4x100(nn.Module):
    """
    Class implementing a network modeling the cost of each action given a state
    """

    def __init__(self, n_states, n_actions, **_):
        """
        Constructor
        :param n_states: the number of components of the Gaussian over latent variables
        :param n_actions: the number of allowable actions
        """

        super().__init__()

        # Create the critic network.
        self.__net = nn.Sequential(
            nn.Linear(n_states, 100),
            nn.ReLU(),
            nn.Linear(100, 100),
            nn.ReLU(),
            nn.Linear(100, 100),
            nn.ReLU(),
            nn.Linear(100, n_actions),
        )

    def forward(self, states):
        """
        Forward pass through the critic network
        :param states: the input states
        :return: the cost of performing each action in that state
        """
        return self.__net(states)


class LinearRelu4x256(nn.Module):
    """
    Class implementing a network modeling the cost of each action given a state
    """

    def __init__(self, n_states, n_actions, **_):
        """
        Constructor
        :param n_states: the number of components of the Gaussian over latent variables
        :param n_actions: the number of allowable actions
        """

        super().__init__()

        # Create the critic network.
        self.__net = nn.Sequential(
            nn.Linear(n_states, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, n_actions),
        )

    def forward(self, states):
        """
        Forward pass through the critic network
        :param states: the input states
        :return: the cost of performing each action in that state
        """
        return self.__net(states)


class LinearReluDropout4x100(nn.Module):
    """
    Class implementing a network modeling the cost of each action given a state
    """

    def __init__(self, n_states, n_actions, **_):
        """
        Constructor
        :param n_states: the number of components of the Gaussian over latent variables
        :param n_actions: the number of allowable actions
        """

        super().__init__()

        # Create the critic network.
        self.__net = nn.Sequential(
            nn.Linear(n_states, 100),
            nn.ReLU(),
            nn.Dropout(),
            nn.Linear(100, 100),
            nn.ReLU(),
            nn.Dropout(),
            nn.Linear(100, 100),
            nn.ReLU(),
            nn.Dropout(),
            nn.Linear(100, n_actions),
        )

    def forward(self, states):
        """
        Forward pass through the critic network
        :param states: the input states
        :return: the cost of performing each action in that state
        """
        return self.__net(states)


class LinearRelu3x128(nn.Module):
    """
    Class implementing a network modeling the cost of each action given a state
    """

    def __init__(self, n_states, n_actions, **_):
        """
        Constructor
        :param n_states: the number of components of the Gaussian over latent variables
        :param n_actions: the number of allowable actions
        """

        super().__init__()

        # Create the critic network.
        self.__net = nn.Sequential(
            nn.Linear(n_states, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, n_actions),
        )

    def forward(self, states):
        """
        Forward pass through the critic network
        :param states: the input states
        :return: the cost of performing each action in that state
        """
        return self.__net(states)
