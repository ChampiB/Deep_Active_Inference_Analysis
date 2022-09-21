from gui.AnalysisConfig import AnalysisConfig


class HostFactory:
    """
    A class allowing the creation of hosts, e.g. LocalComputer or ServerSSH
    """

    conf = AnalysisConfig.instance
    hosts_list = conf.get_all_classes(conf.hosts_directory + "impl/", "hosts.impl.")

    @staticmethod
    def create(key):
        """
        Create the host corresponding to the key passed as parameters
        :param key: the host key
        :return: the created host
        """
        return HostFactory.hosts_list[key]()

