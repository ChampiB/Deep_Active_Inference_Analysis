class DataStorage:
    """
    A class able to store (global) key-value pairs
    """

    store = {}

    @staticmethod
    def register(key, value):
        """
        Register a key-value pair in the store
        :param key: the key
        :param value: the value
        """
        DataStorage.store[key] = value

    @staticmethod
    def get(key):
        """
        Getter
        :param key: the key whose value must be returned
        :return: the value
        """
        return DataStorage.store[key]
