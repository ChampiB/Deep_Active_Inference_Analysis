import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig


class EmptyFrame(tk.Frame):
    """
    A class representing an empty frame
    """

    def __init__(self, parent, file=None):
        """
        Constructor
        :param parent: the parent widget
        :param file: unused
        """

        # Call parent constructor
        super().__init__(parent)

        # Store configuration
        self.conf = AnalysisConfig.instance

        # Change background color
        self.config(background=self.conf.colors["dark_gray"])

    def refresh(self):
        """
        Refresh the empty frame
        """
        pass
