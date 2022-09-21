import json
import os


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
        self.datasets_directory = data_directory + "datasets/"
        self.config_directory = data_directory + "config/"
        self.projects_directory = data_directory + "projects/"
        self.assets_directory = data_directory + "assets/"
        self.agent_forms_directory = data_directory + "../gui/widgets/agent_forms/"
        self.env_forms_directory = data_directory + "../gui/widgets/env_forms/"
        self.pages_directory = data_directory + "../gui/pages/"
        self.frames_directory = data_directory + "../gui/widgets/frames/"
        self.agents_directory = data_directory + "../agents/"
        self.hosts_directory = data_directory + "../hosts/"

        # Load the colors configuration
        colors_file = open(self.config_directory + "colors.json", "r")
        self.colors = json.load(colors_file)

        # Load the font configuration
        font_file = open(self.config_directory + "font.json", "r")
        self.font = json.load(font_file)

        # Load the servers configuration
        server_file = open(self.config_directory + "servers.json", "r")
        self.servers = json.load(server_file)

    @staticmethod
    def get(data_directory=None):
        """
        Getter
        :param data_directory: the directory containing all the data
        :return: the configuration
        """
        if AnalysisConfig.instance is None:
            AnalysisConfig.instance = AnalysisConfig(data_directory)
        return AnalysisConfig.instance

    @staticmethod
    def get_all_classes(path, package):
        """
        Retrieve all the classes within a directory or file
        :param path: the path to the directory or file
        :param package: the classes package
        :return: all the classes
        """
        # Iterate over all files
        classes = {}
        files = os.listdir(path) if os.path.isdir(path) else [os.path.basename(path)]
        for file in files:
            # Check that the file is a python file but not the init.py
            if not file.endswith('.py') or file == '__init__.py':
                continue

            # Get the class and module
            class_name = file[:-3]
            class_module = __import__(package + class_name, fromlist=[class_name])

            # Get the frames' class
            module_dict = class_module.__dict__
            for obj in module_dict:
                if isinstance(module_dict[obj], type) and module_dict[obj].__module__ == class_module.__name__:
                    classes[obj] = getattr(class_module, obj)
        return classes

    @staticmethod
    def get_all_directories(directory):
        """
        Get all directories within a directory
        :param directory: the directory
        :return: all directories
        """
        projects = []
        for entry in os.listdir(directory):
            if os.path.isdir(directory + entry):
                projects.append(entry)
        return projects

    @staticmethod
    def get_all_files(directory):
        """
        Get all files within a directory
        :param directory: the directory
        :return: all files
        """
        files = []
        for entry in os.listdir(directory):
            if os.path.isfile(directory + entry):
                files.append(entry)
        return files
