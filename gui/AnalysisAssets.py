import tkinter as tk


class AnalysisAssets:
    """
    A class that allow the user to access the project's assets
    """

    instance = None

    def __init__(self, assets_directory):
        """
        Constructor
        :param assets_directory: the directory where the assets are stored
        """
        self.images = {
            "run_button": 6,
            "analysis_button": 4,
            "close_button": 13,
            "existing_project_button": 2,
            "new_button": 2,
            "delete_button": 15,
            "server": 6,
            "red_delete_button": 4,
            "black_chevron_down": 8,
            "chevron_right": 9,
            "chevron_down": 9,
            "file": 1,
            "directory": 2,
            "checkbox_off": 6,
            "checkbox_on": 6
        }
        self.photo_images = {}
        self.assets_directory = assets_directory

    @staticmethod
    def get(name=None, subsample=None, assets_directory=None):
        """
        Getter
        :param name: the name of the image to retrieve
        :param subsample: subsample size
        :param assets_directory: the directory where the assets are stored
        :return: the requested image
        """
        # Create assets instance if it does not exist
        if AnalysisAssets.instance is None:
            AnalysisAssets.instance = AnalysisAssets(assets_directory)

        # If no name provided, return
        if name is None:
            return

        # Create the PhotoImage if it does not exist
        size = AnalysisAssets.instance.images[name] if subsample is None else subsample
        if (name, size) not in AnalysisAssets.instance.photo_images.keys():
            file = AnalysisAssets.instance.assets_directory + name + ".png"
            AnalysisAssets.instance.photo_images[name, size] = tk.PhotoImage(file=file).subsample(size, size)

        return AnalysisAssets.instance.photo_images[name, size]

