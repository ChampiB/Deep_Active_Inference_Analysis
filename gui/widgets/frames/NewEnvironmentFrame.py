import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory


class NewEnvironmentFrame(tk.Frame):
    """
    A class allowing to create a new environment
    """

    def __init__(self, parent):
        """
        Constructor
        :param parent: parent widget
        """

        # Call parent constructor
        super().__init__(parent)

        # Save parameters
        self.parent = parent
        self.conf = AnalysisConfig.instance

        # Default project name
        self.default_project_name = "<environment name here>"

        # Place the project renaming frame in the center od the screen
        self.place(relwidth=0.25, relheight=0.175, relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Place the project renaming frame in the center od the screen
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)

        # Change background color
        self.config(background=self.conf.colors["dark_gray"])

        # Add the new project name label
        self.new_project_name_label = LabelFactory.create(self, text="New project name:", theme="dark")
        self.new_project_name_label.grid(row=1, column=0, padx=(10, 0), pady=(5, 10), sticky="nsw")

        # Add the new project name entry
        self.renaming_entry = Entry(self, help_message=self.default_project_name)
        self.renaming_entry.grid(row=1, column=1, columnspan=2, padx=(0, 10), pady=(5, 10), sticky="nsew")
        self.renaming_entry.focus()

    def refresh(self):
        """
        Refresh the new environment frame
        """
        pass
