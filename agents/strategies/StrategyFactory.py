class StrategyFactory:
    """
    A class allowing to create strategy
    """

    @staticmethod
    def create(strategy):
        """
        Create an action selection strategy
        :param strategy: the json describing the strategy
        :return: the created strategy
        """
        module_name = strategy["module"]
        class_name = strategy["class"]
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)(**strategy)
