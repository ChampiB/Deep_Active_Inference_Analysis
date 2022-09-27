import os
from gui.AnalysisAssets import AnalysisAssets
from gui.AnalysisConfig import AnalysisConfig
from gui.DataStorage import DataStorage
from gui.widgets.AnalysisWindow import AnalysisWindow


class AnalysisTool:
    """
    The class used to run the analysis tool.
    """

    def __init__(self, script_file):
        """
        Load the configuration and display the project selection page
        :param script_file: the analysis tool file
        """
        # Get the data directory
        data_dir = os.path.dirname(os.path.abspath(script_file)) + "/data/"

        # Register important objects
        DataStorage.register("tool", self)
        DataStorage.register("conf", AnalysisConfig.get(data_directory=data_dir))
        DataStorage.register("assets", AnalysisAssets.get(assets_directory=AnalysisConfig.instance.assets_directory))
        DataStorage.register("window", AnalysisWindow())

        # Display the initial page
        self.window = DataStorage.get("window")
        self.window.show_page("ProjectSelectionPage")

    def run(self):
        """
        Run the analysis tool
        """
        self.window.mainloop()
