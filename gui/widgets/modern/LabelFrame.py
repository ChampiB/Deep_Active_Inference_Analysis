import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig


class LabelFrame(tk.LabelFrame):
    """
    A class representing modern looking label frame
    """

    def __init__(self, parent, text):
        """
        Constructor
        :param parent: the parent widget
        :param text: the text of the label frame
        """

        self.conf = AnalysisConfig.instance
        super().__init__(
            parent,
            text=text,
            background=self.conf.colors["dark_gray"],
            highlightbackground=self.conf.colors["gray"],
            foreground=self.conf.colors["light_text"],
            font=(self.conf.font["name"], 14, self.conf.font["style"])
        )
