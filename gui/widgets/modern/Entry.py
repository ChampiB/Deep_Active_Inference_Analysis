import tkinter as tk
from tkinter import ttk
from gui.AnalysisConfig import AnalysisConfig


class Entry(ttk.Entry):
    """
    Create a modern entry
    """

    def __init__(self, parent, help_message=""):
        """
        Constructor
        :param parent: the parent widget
        :param help_message: the help message to display before the user start writing text
        """
        # Create the style
        style = ttk.Style(parent)
        style.configure('padded.TEntry', padding=[10, 10, 10, 10])

        # Store configuration
        self.conf = AnalysisConfig.instance

        # Construct the entry
        super().__init__(
            parent, font=(parent.conf.font["name"], 12, parent.conf.font["style"]), style='padded.TEntry',
            foreground=parent.conf.colors["light_text"]
        )

        # Write help message and bind related function
        self.help_message = help_message
        self.insert(tk.END, help_message)
        self.bind("<Key>", self.remove_help_message)
        self.bind("<Button-1>", self.remove_help_message)

    def remove_help_message(self, key=None):
        """
        Remove the help message
        :param key: unused
        """
        if self.help_message == self.get():
            self.delete(0, 'end')
            self.config(foreground=self.conf.colors["dark_text"])

