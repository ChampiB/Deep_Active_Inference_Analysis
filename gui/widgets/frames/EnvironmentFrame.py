import json
import os
import tkinter as tk
from json import JSONDecodeError
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.Combobox import Combobox
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.LabelFrameFactory import LabelFrameFactory
from gui.widgets.modern.Scrollbar import Scrollbar


class EnvironmentFrame(tk.Frame):
    """
    A class allowing to create a new environment
    """

    def __init__(self, parent, file=None):
        """
        Constructor
        :param parent: parent widget
        :param file: the environment file that must be displayed or None if a new environment must be created
        """

        # Call parent constructor
        super().__init__(parent)

        # Save parameters passed as input
        self.parent = parent
        self.conf = AnalysisConfig.instance

        # Load environment from file
        try:
            project_name = parent.master.master.master.project_name
            file_name = self.conf.projects_directory + f"{project_name}/environments/{file}"
            file = open(file_name, "r")
            self.env = json.load(file)
            self.file = file_name
        except (JSONDecodeError, FileNotFoundError):
            self.env = None
            self.file = None

        self.default_env_name = "<environment name here>" if self.env is None else self.env["name"]

        # Get all the agent classes
        self.env_creation_forms = self.conf.get_all_classes(self.conf.env_forms_directory, "gui.widgets.env_forms.")
        self.env_names = [form.replace("Form", "") for form in self.env_creation_forms.keys()]

        # Change background color
        self.config(background=self.conf.colors["dark_gray"])
        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=100)
        self.columnconfigure(2, weight=10)
        self.columnconfigure(3, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        # Create the canvas and scrollbar
        self.canvas = tk.Canvas(self, bg=self.conf.colors["dark_gray"], highlightthickness=0)
        self.canvas.grid(row=0, column=1, sticky="news")
        self.scrollbar = Scrollbar(self, command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=3, sticky='nes')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create the canvas frame
        self.canvas_frame = tk.Frame(self.canvas, background=self.conf.colors["dark_gray"])
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(1, weight=1)
        self.canvas_frame_window = self.canvas.create_window(0, 0, window=self.canvas_frame, anchor='nw')

        # Ask the user to create an agent
        text = "Create a new environment..." if self.env is None else f"Update environment: {self.env['name']}."
        self.new_env_label = LabelFactory.create(self.canvas_frame, text=text, font_size=22, theme="dark")
        self.new_env_label.grid(row=0, column=0, sticky="news", pady=50)

        # Create the general setting box
        self.general_settings = LabelFrameFactory.create(self.canvas_frame, text="General")
        self.general_settings.columnconfigure(0, weight=4, uniform="labelframe")
        self.general_settings.columnconfigure(1, weight=4, uniform="labelframe")
        self.general_settings.columnconfigure(2, weight=1, uniform="labelframe")
        self.general_settings.grid(row=1, column=0, pady=5, padx=5, sticky="nsew")

        self.env_name_label = LabelFactory.create(self.general_settings, text="Name:", theme="dark")
        self.env_name_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")

        self.env_name_entry = Entry(self.general_settings, help_message=self.default_env_name)
        self.env_name_entry.grid(row=0, column=1, pady=5, padx=5, sticky="nsew")

        self.environment_template_label = LabelFactory.create(self.general_settings, text="Template:", theme="dark")
        self.environment_template_label.grid(row=1, column=0, pady=(5, 15), padx=5, sticky="nse")

        text = "SpritesEnvironment" if self.env is None else self.env["class"]
        self.env_template_combo_box = Combobox(
            self.general_settings, self.env_names, command=self.change_env_form, default_value=text
        )
        if file is not None:
            self.env_template_combo_box.lock()
        self.env_template_combo_box.grid(row=1, column=1, pady=(5, 10), padx=5, sticky="nsew")

        self.scrollbar.bind_wheel(self, recursive=True)
        self.env_form = None
        self.change_env_form()
        self.canvas.bind('<Configure>', self.frame_width)

    def frame_width(self, event):
        """
        Configure the canvas frame width
        :param event: the event that triggered the call to this function
        """
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame_window, width=canvas_width)

    def change_env_form(self, event=None):
        """
        Change the agent template
        :param event: unused
        """
        class_name = "Form" + self.env_template_combo_box.get()
        if self.env_form is not None:
            self.env_form.grid_remove()
        self.env_form = self.env_creation_forms[class_name](self.canvas_frame, self.env, self.file)
        self.env_form.columnconfigure(0, weight=1)
        self.env_form.grid(row=2, column=0, pady=5, padx=5, sticky="new")
        self.scrollbar.bind_wheel(self.env_form, recursive=True)
        self.refresh()

    def refresh(self):
        """
        Refresh the new agent frame
        """
        # Update environment form
        self.env_form.refresh()

        # Update buttons frames idle tasks to let tkinter calculate buttons sizes
        self.env_form.update_idletasks()

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    @staticmethod
    def can_update_be_performed(environments_directories, source_file, target_file, env_must_be_created):
        """
        Check whether the update can be applied or not
        :param environments_directories: the directory containing all the environments
        :param source_file: the source file
        :param target_file: the target file
        :param env_must_be_created: True, if an environment must be created, False if it must be updated
        :return: whether the update can be applied or not
        """
        # Get source and target base name
        target_base_name = os.path.basename(target_file)
        source_base_name = os.path.basename(source_file)

        # To create an environment, the target should not exist
        if env_must_be_created and target_base_name in os.listdir(environments_directories):
            print(f"Environment '{source_base_name}' already exist, new environment can't be created.")
            return False

        # To update an environment, the source should exist, but the target should not
        if not env_must_be_created:
            if source_base_name not in os.listdir(environments_directories):
                print(f"Environment source file '{source_base_name}' does not exist, cannot rename environment.")
                return False
            if source_base_name != target_base_name and target_base_name in os.listdir(environments_directories):
                print(f"Environment target file '{target_base_name}' already exist, cannot rename environment.")
                return False
            print(f"Environment '{source_base_name}' will be remove.")
            os.remove(source_file)
        return True
