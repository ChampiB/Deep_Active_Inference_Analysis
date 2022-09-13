import tkinter as tk
from tkinter import ttk
from gui.AnalysisConfig import AnalysisConfig


class Entry(ttk.Entry):
    """
    Create a modern entry
    """

    def __init__(self, parent, valid_input=None, help_message=""):
        """
        Constructor
        :param parent: the parent widget
        :param valid_input: a string describing what a valid input is, e.g., "int", "float", ...
        :param help_message: the help message to display before the user start writing text
        """
        # Create the style
        style = ttk.Style(parent)
        style.configure('padded.TEntry', padding=[10, 10, 10, 10])

        # Store configuration
        self.conf = AnalysisConfig.instance

        # Construct the entry
        super().__init__(
            parent,
            font=(self.conf.font["name"], 12, self.conf.font["style"]),
            style='padded.TEntry',
            foreground=self.conf.colors["light_text"]
        )

        # Check if entry contains an integer
        if valid_input == "int":
            valid_cmd = (self.register(self.is_valid_int), "%P")
            self.config(validate='focusout', validatecommand=valid_cmd)
        # Check if entry contains a float
        if valid_input == "float":
            valid_cmd = (self.register(self.is_valid_float), "%P")
            self.config(validate='focusout', validatecommand=valid_cmd)

        # Write help message and bind related function
        self.help_message = help_message
        self.insert(tk.END, help_message)
        self.bind("<Key>", self.remove_help_message)
        self.bind("<Button-1>", self.remove_help_message)

    def is_valid_int(self, value):
        """
        Check if the value is a valid integer
        :param value: the value being tested
        :return: True, if value is an integer, False otherwise
        """
        try:
            int(value)
            return True
        except ValueError:
            self.delete(0, 'end')
            self.insert(tk.END, self.help_message)
            return False

    def is_valid_float(self, value):
        """
        Check if the value is a valid float
        :param value: the value being tested
        :return: True, if value is a float, False otherwise
        """
        try:
            float(value)
            return True
        except ValueError:
            self.delete(0, 'end')
            self.insert(tk.END, self.help_message)
            return False

    def remove_help_message(self, key=None):
        """
        Remove the help message
        :param key: unused
        """
        if self.help_message == self.get():
            self.delete(0, 'end')
            self.config(foreground=self.conf.colors["dark_text"])

