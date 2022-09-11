import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig


class EmptyFrame(tk.Frame):

    def __init__(self, parent):

        # Call parent constructor
        super().__init__(parent)

        # Store configuration
        self.conf = AnalysisConfig.instance

        # Change background color
        self.config(background=self.conf.colors["dark_gray"])

    def refresh(self):
        pass
