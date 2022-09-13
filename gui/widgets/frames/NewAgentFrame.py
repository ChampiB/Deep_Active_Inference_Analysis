import tkinter as tk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.Combobox import Combobox
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.LabelFrameFactory import LabelFrameFactory
from gui.widgets.modern.Scrollbar import Scrollbar


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
        self.agent_creation_forms = self.conf.get_all_classes(
            self.conf.agent_forms_directory, "gui.widgets.agent_forms."
        )
        self.agent_names = [form.replace("Creation", "") for form in self.agent_creation_forms.keys()]

        # Change background color and configure NewAgentFrame
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
        self.scrollbar.bind_wheel(self)
        self.scrollbar.bind_wheel(self.canvas)

        # Create the canvas frame
        self.canvas_frame = tk.Frame(self.canvas, background=self.conf.colors["dark_gray"])
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(1, weight=1)
        self.canvas_frame_window = self.canvas.create_window(0, 0, window=self.canvas_frame, anchor='nw')
        self.scrollbar.bind_wheel(self.canvas_frame)

        # Ask the user to create an agent
        self.new_agent_label = LabelFactory.create(
            self.canvas_frame, text="Create a new agent...", font_size=22, theme="dark"
        )
        self.new_agent_label.grid(row=0, column=0, sticky="news", pady=50)
        self.scrollbar.bind_wheel(self.new_agent_label)

        # Create the general setting box
        self.general_settings = LabelFrameFactory.create(self.canvas_frame, text="General")
        self.general_settings.columnconfigure(0, weight=4, uniform="labelframe")
        self.general_settings.columnconfigure(1, weight=4, uniform="labelframe")
        self.general_settings.columnconfigure(2, weight=1, uniform="labelframe")
        self.general_settings.grid(row=1, column=0, pady=5, padx=5, sticky="nsew")
        self.scrollbar.bind_wheel(self.general_settings)

        self.agent_name_label = LabelFactory.create(self.general_settings, text="Name:", theme="dark")
        self.agent_name_label.grid(row=0, column=0, pady=5, padx=5, sticky="nse")
        self.scrollbar.bind_wheel(self.agent_name_label)

        self.agent_name_entry = Entry(self.general_settings, help_message="<agent name here>")
        self.agent_name_entry.config(width=250)
        self.agent_name_entry.grid(row=0, column=1, pady=5, padx=5, sticky="nsw")
        self.scrollbar.bind_wheel(self.agent_name_entry)

        self.agent_template_label = LabelFactory.create(self.general_settings, text="Template:", theme="dark")
        self.agent_template_label.grid(row=1, column=0, pady=(5, 15), padx=5, sticky="nse")
        self.scrollbar.bind_wheel(self.agent_template_label)

        self.agent_template_combo_box = Combobox(
            self.general_settings, self.agent_names, command=self.change_agent_form
        )
        self.agent_template_combo_box.grid(row=1, column=1, pady=(5, 10), padx=5, sticky="nsew")
        self.scrollbar.bind_wheel(self.agent_template_combo_box)

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
        class_name = "Creation" + self.agent_template_combo_box.get()
        if self.agent_form is not None:
            self.agent_form.grid_remove()
        self.agent_form = self.agent_creation_forms[class_name](self.canvas_frame, self.scrollbar)
        self.agent_form.columnconfigure(0, weight=1)
        self.agent_form.grid(row=2, column=0, pady=5, padx=5, sticky="new")
        self.scrollbar.bind_wheel(self.agent_form)
        self.refresh()

    def refresh(self):
        """
        Refresh the new agent frame
        """
        # Update agent form idle tasks to let tkinter calculate buttons sizes
        self.agent_form.update_idletasks()

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
