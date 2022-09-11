import os
import tkinter as tk
from gui.AnalysisAssets import AnalysisAssets
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.CheckButton import CheckButton
from gui.widgets.modern.LabelFactory import LabelFactory
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

        self.assets = AnalysisAssets.instance
        self.parent = parent.master.master

        self.projects_directory = self.conf.projects_directory
        self.current_index = 0

        self.selected_entries = []

        self.project_name = ""
        self.widgets = {}  # {"tag": [widget_1, widget_2, ...]}
        self.directories = {}  # {"name": (expanded, files)}

    @staticmethod
    def get_all_files(directory):
        """
        Get all files within a directory
        :param directory: the directory
        :return: all files
        """
        # For each directory in the projects directory
        files = []
        for entry in os.listdir(directory):
            if os.path.isfile(directory + entry):
                files.append(entry)
        return files

    def add_entry(self, entry_name, tag, leaf_node=True, command=None):
        """
        Add an entry to the tree
        :param entry_name: the entry name
        :param tag: the tag (i.e., group containing the entry)
        :param leaf_node: whether the entry is a leaf node
        :param command: the command to call if the user double-click on the entry
        """
        col_index = 0
        if tag not in self.widgets.keys():
            self.widgets[tag] = []

        # Add the button allowing a directory's content to be expanded or hidden
        if not leaf_node:
            button = ButtonFactory.create(self, image=self.assets.get("chevron_down"), theme="light")
            button.config(command=lambda n=entry_name, b=button: self.expand_or_hide_directory(n, b))
            button.grid(row=self.current_index, column=col_index, sticky="w", pady=3, padx=3, ipady=3, ipadx=3)
            self.widgets[tag].append(button)
        col_index += 1

        # Add the entry's name and image
        img = self.assets.get("file") if leaf_node else self.assets.get("directory")
        label = LabelFactory.create(self, image=img, text="  " + entry_name, theme="gray")
        internal_pad_x = 20 if leaf_node else 3
        label.grid(row=self.current_index, column=col_index, sticky="w", pady=3, padx=3, ipady=3, ipadx=internal_pad_x)
        if command is not None:
            label.bind('<Double-Button-1>', command)
        self.widgets[tag].append(label)
        col_index += 1

        # Add the selection checkbox for leaf nodes
        if leaf_node:
            checkbox_var = tk.IntVar()
            checkbox = CheckButton(
                self, variable=checkbox_var,
                command=lambda f=entry_name, d=tag: self.update_selected_entries(checkbox_var, f, d)
            )
            checkbox.grid(row=self.current_index, column=col_index, sticky="e", pady=3, padx=(3, 10), ipady=3, ipadx=3)
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

    def display_directory(self, dir_name, files, allow_creation_of=None):
        """
        Display a directory in the tree structure
        :param dir_name: the directory's name
        :param files: the files in the directory
        :param allow_creation_of: the entry type whose creation should be allowed the i.e., "agents" or "environments"
        """
        self.add_entry(dir_name, dir_name + "/", leaf_node=False)
        self.current_index += 1
        for file in files:
            self.add_entry(file, dir_name, command=lambda event, d=dir_name, f=file: self.display_details(event, d, f))
            self.current_index += 1
        if allow_creation_of == "agents":
            self.add_new_agent_entry(dir_name)
            self.current_index += 1
        if allow_creation_of == "environments":
            self.add_new_environments_entry(dir_name)
            self.current_index += 1

    def update_directory(self, dir_name):
        """
        Display a directory in the tree structure, without creating it
        :param dir_name: the directory's name
        """
        if dir_name not in self.widgets.keys():
            return
        if self.directories[dir_name][0]:
            for widget in self.widgets[dir_name]:
                widget.grid()
        else:
            for widget in self.widgets[dir_name]:
                widget.grid_remove()

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
            self, image=self.assets.get("new_button", subsample=17), theme="light",
            command=lambda n="NewAgentFrame": self.parent.show_frame(n)
        )
        button.grid(row=self.current_index, column=1, sticky="w", pady=(0, 3), padx=(15, 3))
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
            self, image=self.assets.get("new_button", subsample=17), theme="light",
            command=lambda n="NewEnvironmentFrame": self.parent.show_frame(n)
        )
        button.grid(row=self.current_index, column=1, sticky="w", pady=(0, 3), padx=(15, 3))
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

        if project != self.project_name:
            # Forget old widgets, directories and selected entries
            for widgets in self.widgets.values():
                for widget in widgets:
                    widget.grid_forget()
            self.widgets.clear()
            self.directories.clear()
            self.selected_entries = []

            # Load new agents and environments
            agents = self.get_all_files(self.projects_directory + project + "/agents/")
            self.directories["Agents"] = (True, agents)
            environments = self.get_all_files(self.projects_directory + project + "/environments/")
            self.directories["Environments"] = (True, environments)

            # Display directories
            for directory, (_, files) in self.directories.items():
                self.display_directory(directory, files, allow_creation_of=directory.lower())

            # Set project name
            self.project_name = project

            # Reset the parent's frame
            self.parent.show_frame("EmptyFrame")
        else:
            # Update directories
            for directory in self.directories.keys():
                self.update_directory(directory)

    def display_details(self, event, directory, file):
        """
        Display the details of the entry
        :param event: unused
        :param directory: the directory whose details should be displayed
        :param file: the file whose details should be displayed
        """
        print(f"display_details({directory}, {file})")  # TODO
