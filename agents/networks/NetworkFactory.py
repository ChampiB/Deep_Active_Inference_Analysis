class NetworkFactory:
    """
    A class allowing to create networks
    """

    @staticmethod
    def create(network):
        """
        Create a network
        :param network: the json describing the network
        :return: the created network
        """
        module_name = network["module"]
        class_name = network["class"]
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)(**network)
