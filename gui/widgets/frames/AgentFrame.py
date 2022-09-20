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


class AgentFrame(tk.Frame):
    """
    A class allowing to create a new agent
    """

    def __init__(self, parent, file):
        """
        Constructor
        :param parent: parent widget
        :param file: the agent file that must be displayed or None if a new agent must be created
        """

        # Call parent constructor
        super().__init__(parent)

        # Save parameters passed as input
        self.parent = parent
        self.conf = AnalysisConfig.instance

        # Load agent from file
        try:
            project_name = parent.master.master.master.project_name
            file_name = self.conf.projects_directory + f"{project_name}/agents/{file}"
            file = open(file_name, "r")
            self.agent = json.load(file)
            self.file = file_name
        except (JSONDecodeError, FileNotFoundError):
            self.agent = None
            self.file = None

        self.default_agent_name = "<agent name here>" if self.agent is None else self.agent["name"]

        # Get all the agent classes
        self.agent_creation_forms = self.conf.get_all_classes(
            self.conf.agent_forms_directory, "gui.widgets.agent_forms."
        )
        self.agent_names = [form.replace("Form", "") for form in self.agent_creation_forms.keys()]

        # Change background color and configure AgentFrame
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
        text = "Create a new agent..." if self.agent is None else f"Update agent: {self.agent['name']}."
        self.new_agent_label = LabelFactory.create(self.canvas_frame, text=text, font_size=22, theme="dark")
        self.new_agent_label.grid(row=0, column=0, sticky="news", pady=50)

        # Create the general setting box
        self.general_settings = LabelFrameFactory.create(self.canvas_frame, text="General")
        self.general_settings.columnconfigure(0, weight=4, uniform="labelframe")
        self.general_settings.columnconfigure(1, weight=4, uniform="labelframe")
        self.general_settings.columnconfigure(2, weight=1, uniform="labelframe")
        self.general_settings.grid(row=1, column=0, pady=5, padx=5, sticky="nsew")

        self.agent_name_label = LabelFactory.create(self.general_settings, text="Name:", theme="dark")
        self.agent_name_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")

        self.agent_name_entry = Entry(self.general_settings, help_message=self.default_agent_name)
        self.agent_name_entry.config(width=250)
        self.agent_name_entry.grid(row=0, column=1, pady=5, padx=5, sticky="nsw")

        self.agent_template_label = LabelFactory.create(self.general_settings, text="Template:", theme="dark")
        self.agent_template_label.grid(row=1, column=0, pady=(5, 15), padx=5, sticky="nse")

        text = "HMM" if self.agent is None else self.agent["class"]
        self.agent_template_combo_box = Combobox(
            self.general_settings, self.agent_names, command=self.change_agent_form, default_value=text
        )
        self.agent_template_combo_box.grid(row=1, column=1, pady=(5, 10), padx=5, sticky="nsew")
        if file is not None:
            self.agent_template_combo_box.lock()

        self.scrollbar.bind_wheel(self, recursive=True)
        self.agent_form = None
        self.change_agent_form()
        self.canvas.bind('<Configure>', self.frame_width)

    def frame_width(self, event):
        """
        Configure the canvas frame width
        :param event: the event that triggered the call to this function
        """
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame_window, width=canvas_width)

    def change_agent_form(self, event=None):
        """
        Change the agent template
        :param event: unused
        """
        class_name = "Form" + self.agent_template_combo_box.get()
        if self.agent_form is not None:
            self.agent_form.grid_remove()
        self.agent_form = self.agent_creation_forms[class_name](self.canvas_frame, self.agent, self.file)
        self.agent_form.columnconfigure(0, weight=1)
        self.agent_form.grid(row=2, column=0, pady=5, padx=5, sticky="new")
        self.scrollbar.bind_wheel(self.agent_form, recursive=True)
        self.refresh()

    def refresh(self):
        """
        Refresh the new agent frame
        """
        # Update agent form
        self.agent_form.refresh()

        # Update agent form idle tasks to let tkinter calculate buttons sizes
        self.agent_form.update_idletasks()

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    @staticmethod
    def can_update_be_performed(agents_directories, source_file, target_file, agent_must_be_created):
        """
        Check whether the update can be applied or not
        :param agents_directories: the directory containing all the agents
        :param source_file: the source file
        :param target_file: the target file
        :param agent_must_be_created: True, if an agent must be created, False if it must be updated
        :return: whether the update can be applied or not
        """
        # Get source and target base name
        target_base_name = os.path.basename(target_file)
        source_base_name = os.path.basename(source_file)

        # To create an agent, the target should not exist
        if agent_must_be_created and target_base_name in os.listdir(agents_directories):
            print(f"Agent '{source_base_name}' already exist, new agent can't be created.")
            return False

        # To update an agent, the source should exist, but the target should not
        if not agent_must_be_created:
            if source_base_name not in os.listdir(agents_directories):
                print(f"Agent source file '{source_base_name}' does not exist, cannot rename agent.")
                return False
            if source_base_name != target_base_name and target_base_name in os.listdir(agents_directories):
                print(f"Agent target file '{target_base_name}' already exist, cannot rename agent.")
                return False
            print(f"Agent '{source_base_name}' will be remove.")
            os.remove(source_file)
        return True

    def stop(self):
        """
        Stop all tasks running in background
        """
        pass
