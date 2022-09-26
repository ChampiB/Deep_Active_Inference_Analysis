from gui.AnalysisConfig import AnalysisConfig


class HostFactory:
    """
    A class allowing the creation of hosts, e.g. LocalComputer or ServerSSH
    """

    conf = AnalysisConfig.instance
    hosts_list = conf.get_all_classes(conf.hosts_directory + "impl/", "hosts.impl.")

    @staticmethod
    def create(key, params):
        """
        Create the host corresponding to the key passed as parameters
        :param key: the host key
        :param params: the host parameters
        :return: the created host
        """
        return HostFactory.hosts_list[key](key, **params)
