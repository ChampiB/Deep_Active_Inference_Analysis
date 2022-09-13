import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.Combobox import Combobox
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.LabelFrame import LabelFrame


class NewAgentFrame(tk.Frame):
    """
    A class allowing to create a new agent
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

        # Get all the agent classes
        self.agent_creation_forms = self.conf.get_all_classes(self.conf.agent_forms_directory, "gui.widgets.forms.")
        self.agent_names = [form.replace("Creation", "") for form in self.agent_creation_forms.keys()]

        # Change background color
        self.config(background=self.conf.colors["dark_gray"])
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=4)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(2, weight=1)

        # Ask the user to create an agent
        self.new_agent_label = LabelFactory.create(self, text="Create a new agent...", font_size=22, theme="dark")
        self.new_agent_label.grid(row=0, column=1, sticky="news", pady=50)

        # Create the general setting box
        self.general_settings = LabelFrame(self, text="General")
        self.general_settings.grid(row=1, column=1, ipady=4, sticky="news")
        self.general_settings.columnconfigure(0, weight=3, uniform="labelframe")
        self.general_settings.columnconfigure(1, weight=5, uniform="labelframe")

        self.agent_name_label = LabelFactory.create(self.general_settings, text="Name:", theme="dark")
        self.agent_name_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")

        self.agent_name_entry = Entry(self.general_settings, help_message="<agent name here>")
        self.agent_name_entry.grid(row=0, column=1, pady=5, padx=(5, 500), sticky="nsew")

        self.agent_template_label = LabelFactory.create(self.general_settings, text="Template:", theme="dark")
        self.agent_template_label.grid(row=1, column=0, pady=(5, 15), padx=5, sticky="nse")

        self.agent_template_combo_box = Combobox(self.general_settings, self.agent_names, self.change_agent_form)
        self.agent_template_combo_box.grid(row=1, column=1, pady=(5, 10), padx=(5, 500), sticky="nsew")

        self.agent_form = None
        self.change_agent_form()

    def change_agent_form(self, event=None):
        """
        Change the agent template
        :param event: unused
        """
        class_name = "Creation" + self.agent_template_combo_box.get()
        self.agent_form = self.agent_creation_forms[class_name](self)
        self.agent_form.columnconfigure(0, weight=1)
        self.agent_form.grid(row=2, column=1, ipady=4, sticky="nsew")

    def refresh(self):
        """
        Refresh the new agent frame
        """
        pass
