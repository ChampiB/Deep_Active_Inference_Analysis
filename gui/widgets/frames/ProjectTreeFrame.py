import tkinter as tk
from threading import Timer

from gui.AnalysisAssets import AnalysisAssets
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.CheckButton import CheckButton
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.Scrollbar import Scrollbar
from gui.widgets.modern.ToolTip import ToolTip


class ProjectTreeFrame(tk.Frame):
    """
    A class representing the project tree structure
    """

    def __init__(self, parent):
        """
        Constructor
        :param parent: the parent widget
        """

        # Store config and window
        self.conf = AnalysisConfig.instance

        # Call parent constructor
        super().__init__(parent, background=self.conf.colors["gray"])

        # Configure row and columns weights
        self.columnconfigure(0, weight=50)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Initialise class attributes
        self.assets = AnalysisAssets.instance
        self.parent = parent.master.master

        self.projects_directory = self.conf.projects_directory
        self.current_index = 0

        self.selected_entries = []

        self.project_name = ""
        self.widgets = {}  # {"tag": [widget_1, widget_2, ...]}
        self.directories = {}  # {"name": (expanded, files)}

        # Create the canvas and scrollbar
        self.canvas = tk.Canvas(self, bg=self.conf.colors["gray"], highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="news")
        self.scrollbar = Scrollbar(self, command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='nes')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.bind_wheel(self)
        self.scrollbar.bind_wheel(self.canvas)

        # Create the canvas frame
        self.canvas_frame = tk.Frame(self.canvas, background=self.conf.colors["gray"])
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame_window = self.canvas.create_window(0, 0, window=self.canvas_frame, anchor='nw')
        self.scrollbar.bind_wheel(self.canvas_frame)

    def add_entry(self, entry_name, tag, leaf_node=True, expanded=True, command=None):
        """
        Add an entry to the tree
        :param entry_name: the entry name
        :param tag: the tag (i.e., group containing the entry)
        :param leaf_node: whether the entry is a leaf node
        :param command: the command to call if the user double-click on the entry
        :param expanded: whether the directory is expanded
        """
        col_index = 0
        if tag not in self.widgets.keys():
            self.widgets[tag] = []

        # Add the button allowing a directory's content to be expanded or hidden
        if not leaf_node:
            img = self.assets.get("chevron_down") if expanded else self.assets.get("chevron_right")
            button = ButtonFactory.create(self.canvas_frame, image=img, theme="light")
            button.config(command=lambda n=entry_name, b=button: self.expand_or_hide_directory(n, b))
            button.grid(row=self.current_index, column=col_index, sticky="w", pady=3, padx=3, ipady=3, ipadx=3)
            self.scrollbar.bind_wheel(button)
            self.widgets[tag].append(button)
        col_index += 1

        # Add the entry's name and image
        img = self.assets.get("file") if leaf_node else self.assets.get("directory")
        label = LabelFactory.create(self.canvas_frame, image=img, text="  " + entry_name, theme="gray")
        internal_pad_x = 20 if leaf_node else 3
        label.grid(row=self.current_index, column=col_index, sticky="w", pady=3, padx=3, ipady=3, ipadx=internal_pad_x)
        self.scrollbar.bind_wheel(label)
        if command is not None:
            label.bind('<Double-Button-1>', command)
        self.widgets[tag].append(label)
        col_index += 1

        # Add the selection checkbox for leaf nodes
        if leaf_node:
            checkbox_var = tk.IntVar()
            checkbox = CheckButton(
                self.canvas_frame, variable=checkbox_var,
                command=lambda f=entry_name, d=tag: self.update_selected_entries(checkbox_var, f, d)
            )
            checkbox.grid(row=self.current_index, column=col_index, sticky="e", pady=3, padx=(3, 10), ipady=3, ipadx=3)
            self.scrollbar.bind_wheel(checkbox)
            self.columnconfigure(col_index, weight=1)
            self.widgets[tag].append(checkbox)
            col_index += 1

    def update_selected_entries(self, checkbox_var, f, d):
        """
        Update the selected by adding or removing the file-directory pair depending on the checkbox state
        :param checkbox_var: the checkbox state
        :param f: the file name
        :param d: the directory name
        """
        if checkbox_var.get():
            self.selected_entries.append((d, f))
        else:
            if (d, f) in self.selected_entries:
                self.selected_entries.remove((d, f))

    def display_directory(self, dir_name, files, allow_creation_of=None, expanded=True):
        """
        Display a directory in the tree structure
        :param dir_name: the directory's name
        :param files: the files in the directory
        :param allow_creation_of: the entry type whose creation should be allowed the i.e., "agents" or "environments"
        :param expanded: whether the directory is expanded
        """
        self.add_entry(dir_name, dir_name + "/", leaf_node=False, expanded=expanded)
        self.current_index += 1
        if not expanded:
            return
        for file in files:
            self.add_entry(file, dir_name, command=lambda event, d=dir_name, f=file: self.display_details(event, d, f))
            self.current_index += 1
        if allow_creation_of == "agents":
            self.add_new_agent_entry(dir_name)
            self.current_index += 1
        if allow_creation_of == "environments":
            self.add_new_environments_entry(dir_name)
            self.current_index += 1

    def expand_or_hide_directory(self, directory_name, button):
        """
        Allows to expand or hide a directory within the tree structure
        :param directory_name: the directory name to expand or hide
        :param button: the button whose image should be updated
        """
        (expanded, files) = self.directories[directory_name]
        expanded = not expanded
        self.directories[directory_name] = (expanded, files)
        button.config(
            image=self.assets.get("chevron_down") if expanded else self.assets.get("chevron_right")
        )
        self.refresh(self.project_name)

    def add_new_agent_entry(self, tag):
        """
        Add an entry allowing to create a new agent
        :param tag: the entry tag (i.e., group)
        """
        button = ButtonFactory.create(
            self.canvas_frame, image=self.assets.get("new_button", subsample=17), theme="light",
            command=lambda n="NewAgentFrame": self.parent.show_frame(n)
        )
        button.grid(row=self.current_index, column=1, sticky="w", pady=(0, 3), padx=(15, 3))
        self.scrollbar.bind_wheel(button)
        ToolTip(button, f"Create a new agent")
        if tag not in self.widgets.keys():
            self.widgets[tag] = [button]
        else:
            self.widgets[tag].append(button)

    def add_new_environments_entry(self, tag):
        """
        Add an entry allowing to create a new environment
        :param tag: the entry tag (i.e., group)
        """
        button = ButtonFactory.create(
            self.canvas_frame, image=self.assets.get("new_button", subsample=17), theme="light",
            command=lambda n="NewEnvironmentFrame": self.parent.show_frame(n)
        )
        button.grid(row=self.current_index, column=1, sticky="w", pady=(0, 3), padx=(15, 3))
        self.scrollbar.bind_wheel(button)
        ToolTip(button, f"Create a new environment")
        if tag not in self.widgets.keys():
            self.widgets[tag] = [button]
        else:
            self.widgets[tag].append(button)

    def refresh(self, project):
        """
        Refresh the project tree structure
        :param project: the current project name
        """
        self.current_index = 0

        # Forget old widgets, directories and selected entries
        for widgets in self.widgets.values():
            for widget in widgets:
                widget.grid_forget()
        self.widgets.clear()
        self.selected_entries = []

        # Load new agents and environments
        agents = self.conf.get_all_files(self.projects_directory + project + "/agents/")
        expanded = self.directories["Agents"][0] if "Agents" in self.directories.keys() else True
        self.directories["Agents"] = (expanded, agents)
        environments = self.conf.get_all_files(self.projects_directory + project + "/environments/")
        expanded = self.directories["Environments"][0] if "Environments" in self.directories.keys() else True
        self.directories["Environments"] = (expanded, environments)

        # Display directories
        for directory, (expanded, files) in self.directories.items():
            self.display_directory(directory, files, allow_creation_of=directory.lower(), expanded=expanded)

        # Set project name
        self.project_name = project

        # Update buttons frames idle tasks to let tkinter calculate buttons sizes
        self.canvas_frame.update_idletasks()

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # Change width of first column in PannedWindow
        Timer(0.1, self.set_panned_window_width).start()

        # Reset the parent's frame
        self.parent.show_frame("EmptyFrame")

    def set_panned_window_width(self):
        width = self.canvas_frame.winfo_width() + 15
        if self.scrollbar.is_hidden():
            width -= 15
        self.parent.project_window.sash_place(0, width, 0)

    def display_details(self, event, directory, file):
        """
        Display the details of the entry
        :param event: unused
        :param directory: the directory whose details should be displayed
        :param file: the file whose details should be displayed
        """
        print(f"display_details({directory}, {file})")  # TODO
