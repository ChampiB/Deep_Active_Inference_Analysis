from gui.AnalysisAssets import AnalysisAssets
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.AnalysisWindow import AnalysisWindow


class AnalysisTool:
    """
    The class used to run the analysis tool.
    """

    def __init__(self, data_directory):
        """
        Load the configuration and display the project selection page
        :param data_directory: the data directory
        """
        # Create the configuration and assets instances
        AnalysisConfig.get(data_directory=data_directory)
        AnalysisAssets.get(assets_directory=AnalysisConfig.instance.assets_directory)

        # Create the main window and display the initial page
        self.window = AnalysisWindow()
        self.window.show_page("ProjectSelectionPage")

    def run(self):
        """
        Run the analysis tool
        """
        self.window.mainloop()
