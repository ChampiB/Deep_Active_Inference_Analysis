import os
import json
import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.Combobox import Combobox
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.LabelFrameFactory import LabelFrameFactory
from gui.widgets.modern.ToolTip import ToolTip


class CreationSpritesEnvironment(tk.Frame):
    """
    A creation form for a dSprites environment
    """

    def __init__(self, parent, scrollbar):
        """
        Constructor
        :param parent: the parent widget
        :param scrollbar: the scrollbar widget allowing to scroll the creation form
        """
        super().__init__(parent)
        self.conf = AnalysisConfig.instance
        self.config(background=self.conf.colors["dark_gray"])
        self.parent = parent.master.master
        self.project_page = self.parent.master.master.master.master

        # Create characteristics label frame
        self.characteristics = LabelFrameFactory.create(self, text="Characteristics")
        CreationSpritesEnvironment.configure_columns(self.characteristics)
        self.characteristics.grid(row=0, column=0, pady=15, sticky="nsew")
        scrollbar.bind_wheel(self.characteristics)

        self.difficulty_label = LabelFactory.create(self.characteristics, text="Difficulty:", theme="dark")
        self.difficulty_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.difficulty_label)

        self.difficulty_combobox = Combobox(self.characteristics, values=["Easy", "Hard"], default_value="Hard")
        self.difficulty_combobox.grid(row=0, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.difficulty_combobox)

        self.max_trial_length_label = LabelFactory.create(
            self.characteristics, text="Maximum number of steps per trials:", theme="dark"
        )
        self.max_trial_length_label.grid(row=1, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.max_trial_length_label)

        self.max_trial_length_entry = Entry(self.characteristics, valid_input="int", help_message="50")
        self.max_trial_length_entry.grid(row=1, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.max_trial_length_entry)

        self.n_repeats_label = LabelFactory.create(
            self.characteristics, text="Number of times an actions is repeated:", theme="dark"
        )
        self.n_repeats_tooltip = ToolTip(
            self.n_repeats_label,
            text="Each time the agent performs an action, it will be executed several times in the environments"
        )
        self.n_repeats_label.grid(row=2, column=0, pady=5, padx=5, sticky="nse")
        scrollbar.bind_wheel(self.n_repeats_label)

        self.n_repeats_entry = Entry(self.characteristics, valid_input="int", help_message="5")
        self.n_repeats_entry.grid(row=2, column=1, pady=5, padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.n_repeats_entry)

        self.epistemic_label = LabelFactory.create(self.characteristics, text="Epistemic task:", theme="dark")
        self.epistemic_label.grid(row=3, column=0, pady=(5, 15), padx=5, sticky="nse")
        scrollbar.bind_wheel(self.epistemic_label)

        self.epistemic_combobox = Combobox(self.characteristics, values=["True", "False"], default_value="True")
        self.epistemic_combobox.grid(row=3, column=1, pady=(5, 15), padx=5, sticky="nsew")
        scrollbar.bind_wheel(self.epistemic_combobox)

        # Create the create button
        self.create_button = ButtonFactory.create(self, text="Create", theme="blue", command=self.create_sprites_env)
        self.create_button.grid(row=1, column=0, pady=15, ipady=5, ipadx=5, sticky="nse")
        scrollbar.bind_wheel(self.create_button)

    @staticmethod
    def configure_columns(widget):
        """
        Configure the widget columns
        :param widget: the widget
        """
        widget.columnconfigure(0, weight=4, uniform="labelframe")
        widget.columnconfigure(1, weight=4, uniform="labelframe")
        widget.columnconfigure(2, weight=1, uniform="labelframe")

    def create_sprites_env(self):
        """
        Create the environment file on the file system
        """
        # Get environments requested by users
        env_name = self.parent.env_name_entry.get()

        # Get environment directory and file name
        environments_directories = self.conf.projects_directory + self.project_page.project_name + "/environments/"
        file_name = env_name + ".json"

        # Check that the project does not exist
        if file_name in os.listdir(environments_directories):
            print(f"Environment '{file_name}' already exist.")
            return

        # Write the description of the new agent on the filesystem
        file = open(environments_directories + file_name, "a")
        json.dump({
            "name": env_name,
            "module": "environments.impl.SpritesEnvironment",
            "class": "SpritesEnvironment",
            "difficulty": self.difficulty_combobox.get(),
            "max_trial_length": self.max_trial_length_entry.get(),
            "n_repeats": self.n_repeats_entry.get(),
            "epistemic": self.epistemic_combobox.get(),
        }, file, indent=2)

        # Refresh project tree and display empty frame in the project page
        self.project_page.project_tree.refresh(self.project_page.project_name)
        self.project_page.show_frame("EmptyFrame")
