import tkinter as tk
from gui.AnalysisAssets import AnalysisAssets
from gui.AnalysisConfig import AnalysisConfig


class CheckButton(tk.Checkbutton):
    """
    A modern checkbutton
    """

    def __init__(self, parent, variable, command):
        """
        Constructor
        :param parent: the parent widget
        :param variable: the checkbutton variable defining its state
        :param command: the callback function to call when the combo-box's value has changed
        """

        self.assets = AnalysisAssets.instance
        self.conf = AnalysisConfig.instance

        super().__init__(
            parent,
            image=self.assets.get("checkbox_off"),
            selectimage=self.assets.get("checkbox_on"),
            foreground=self.conf.colors["blue"],
            borderwidth=0,
            highlightbackground=self.conf.colors["gray"],
            background=self.conf.colors["gray"],
            activebackground=self.conf.colors["light_gray"],
            selectcolor=self.conf.colors["gray"],
            variable=variable,
            indicatoron=False,
            command=command
        )
