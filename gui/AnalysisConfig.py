import json


class AnalysisConfig:
    """
    The class loading the configuration.
    """

    instance = None

    def __init__(self, data_directory):
        """
        Load all the configuration files
        :param data_directory: the data directory
        """
        # Get the configuration directory
        self.data_directory = data_directory
        self.config_directory = data_directory + "config/"
        self.projects_directory = data_directory + "projects/"
        self.assets_directory = data_directory + "assets/"
        self.agents_directory = data_directory + "../agents/"

        # Load the colors configuration
        colors_file = open(self.config_directory + "colors.json", "r")
        self.colors = json.load(colors_file)

        # Load the font configuration
        font_file = open(self.config_directory + "font.json", "r")
        self.font = json.load(font_file)

    @staticmethod
    def get(data_directory=None):
        if AnalysisConfig.instance is None:
            AnalysisConfig.instance = AnalysisConfig(data_directory)
        return AnalysisConfig.instance
