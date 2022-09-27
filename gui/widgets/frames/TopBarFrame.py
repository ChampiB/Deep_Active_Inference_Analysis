import json
import os
import tkinter as tk
from gui.AnalysisAssets import AnalysisAssets
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.frames.EmptyFrame import EmptyFrame
from gui.widgets.frames.ProjectRenamingFrame import ProjectRenamingFrame
from gui.widgets.frames.ServerConfigurationFrame import ServerConfigurationFrame
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.Combobox import Combobox
from gui.widgets.modern.ToolTip import ToolTip
from hosts.HostFactory import HostFactory


class TopBarFrame(tk.Frame):
    """
    A class representing the top bar of the analysis tool
    """

    def __init__(
        self, parent, display_delete_button=True, display_project_name=True, display_run_button=True,
        display_server_button=True, display_analysis_button=True, command="go_to_project_selection_page"
    ):
        """
        Constructor
        :param parent: the parent widget
        :param display_server_button: whether to display the server button
        :param display_project_name: whether to display the project name
        :param display_run_button:  whether to display the run button
        :param display_analysis_button: whether to display the analysis button
        :param command: the command to call when clicking on the close button
        """
        # Call parent constructor
        super().__init__(parent, background=parent.conf.colors["dark_gray"])

        # Store parent, configuration and assets
        self.parent = parent
        self.conf = AnalysisConfig.instance
        self.assets = AnalysisAssets.instance

        # The column index
        col_index = 0

        # Add project name label
        self.name_label = None
        if display_project_name:
            self.name_label = ButtonFactory.create(
                self, text=parent.project_name, command=self.ask_new_project_name, font_size=12
            )
            self.description_tooltip = ToolTip(self.name_label, text="")
            self.name_label.grid(row=0, column=col_index, padx=6, pady=6)
            col_index += 1

        # Add the button for ssh server specification
        self.training_location = None
        if display_server_button:
            self.new_button = self.assets.get("new_button", subsample=16)
            new_server = {"image": self.new_button, "text": "new ssh server", "command": self.ask_new_server}
            default_value = self.get_project_from_filesystem()
            if default_value is not None:
                default_value = default_value["host"]
            self.server_combobox = Combobox(
                self, values=list(self.conf.servers.keys()) + [new_server], default_value=default_value,
                theme="dark", image=self.assets.get("server"), command=self.update_default_host
            )
            self.server_combobox.grid(row=0, column=col_index, padx=(0, 10), pady=(3, 0), ipadx=1, ipady=1)
            col_index += 1

        # Add the run button
        if display_run_button:
            self.run_button = ButtonFactory.create(self, image=self.assets.get("run_button"), command=self.train)
            self.run_button.grid(row=0, column=col_index, padx=3, pady=3, ipadx=6, ipady=3)
            text = f"Run training" if self.training_location is None else f"Run training '{self.training_location}'"
            self.run_button_tip = ToolTip(self.run_button, text)
            col_index += 1

        # Add the analysis button
        if display_analysis_button:
            self.analysis_button = ButtonFactory.create(self, image=self.assets.get("analysis_button"))
            self.analysis_button.grid(row=0, column=col_index, padx=3, pady=3, ipadx=3, ipady=3)
            self.analysis_button_tip = ToolTip(self.analysis_button, f"Run analysis")
            col_index += 1

        # Add the delete button
        if display_delete_button:
            self.delete_button = ButtonFactory.create(
                self, image=self.assets.get("red_delete_button"), command=self.delete_selection
            )
            self.delete_button.grid(row=0, column=col_index, padx=3, pady=3, ipadx=4, ipady=3)
            self.delete_button_tip = ToolTip(self.delete_button, f"Delete")
            col_index += 1

        # Add empty widget
        self.grid_columnconfigure(col_index, weight=1)
        self.empty_widget = EmptyFrame(self)
        self.empty_widget.grid(row=0, column=col_index, pady=10, padx=10, sticky="we")
        col_index += 1

        # Add closing button
        command = getattr(self, command)
        self.closing_button = ButtonFactory.create(self, image=self.assets.get("close_button"), command=command)
        self.closing_button.grid(row=0, column=col_index, pady=10, padx=10, sticky="we")
        col_index += 1

        # Frame for renaming the project, and frame for server configuration
        self.project_renaming_frame = None
        self.server_configuration_frame = None

    def train(self):
        """
        Train the agents on the environments
        """
        # Hide the tip
        self.run_button_tip.hidetip()

        # Get the agents and environments
        agents = []
        environments = []
        for entry_type, entry_file in self.parent.project_tree.selected_entries:
            if entry_type == "Agents":
                agents.append(entry_file)
            if entry_type == "Environments":
                environments.append(entry_file)

        # Check that there is at least one agent and one environment
        if len(agents) == 0 or len(environments) == 0:
            print("At least on agent and one environment is required for training to be successful.")
            self.parent.show_frame("JobStatusFrame")
            return

        # Get the host
        server_name = self.server_combobox.get()
        host_json = self.conf.servers[server_name]
        host_json["server_name"] = server_name
        host = HostFactory.create(host_json["class"], host_json)

        # Train the agents on the environment
        for agent in agents:
            for env in environments:
                host.train(agent, env, self.parent.project_name)

        # Display job status frame
        self.parent.show_frame("JobStatusFrame", {"agents": agents, "environments": environments})

    def go_to_project_selection_page(self):
        """
        Show the project selection page
        """
        self.parent.window.show_page("ProjectSelectionPage")

    def quit(self):
        """
        Close the application
        """
        self.parent.window.close()

    def ask_new_project_name(self, event=None):
        """
        Ask the user for the new project name
        :param event: unused
        """
        if self.project_renaming_frame is None or not self.project_renaming_frame.winfo_viewable():
            # Forget server configuration frame
            if self.server_configuration_frame is not None:
                self.server_configuration_frame.place_forget()

            # Display project renaming frame
            self.project_renaming_frame = ProjectRenamingFrame(self.parent)

    def ask_new_server(self, event=None):
        """
        Ask the user for the new server configuration
        :param event: unused
        """
        self.server_combobox.list_values_widget.withdraw()
        if self.server_configuration_frame is None or not self.server_configuration_frame.winfo_viewable():
            # Forget project renaming frame
            if self.project_renaming_frame is not None:
                self.project_renaming_frame.place_forget()

            # Display server configuration frame
            self.server_configuration_frame = ServerConfigurationFrame(self.parent)

    def update_servers(self):
        """
        Update the servers list
        """
        # Update file system
        server_file = self.conf.config_directory + "servers.json"
        server_file = open(server_file, "w")
        json.dump(self.conf.servers, server_file, indent=2)

        # Update combobox values
        new_server = {"image": self.new_button, "text": "new ssh server", "command": self.ask_new_server}
        values = list(self.conf.servers.keys()) + [new_server]
        self.server_combobox.set_values(values)

        # Update default host
        self.update_default_host()

    def update_default_host(self):
        """
        Update the default project host
        :return:
        """
        project = self.get_project_from_filesystem()
        project["host"] = self.server_combobox.get()
        project_file = self.conf.projects_directory + self.parent.project_name + "/project.json"
        json.dump(project, open(project_file, "w"), indent=2)

    def refresh(self, project, description=None):
        """
        Refresh the top bar of the analysis tool
        :param project: the project name to display
        :param description: the project description
        """
        self.name_label.config(text=project)
        self.description_tooltip.text = description
        default_value = self.get_project_from_filesystem()
        if default_value is not None:
            default_value = default_value["host"]
        self.server_combobox.current_value.set(default_value)

    def delete_selection(self):
        """
        Delete the selected agents and environments
        """
        # If no selection select the currently selected host
        if len(self.parent.project_tree.selected_entries) == 0:
            host = self.server_combobox.get()
            if host != "local computer":
                del self.conf.servers[host]
                self.update_servers()
            return

        # Else delete selection
        for dir_name, file_name in self.parent.project_tree.selected_entries:
            os.remove(self.conf.projects_directory + f"{self.parent.project_name}/{dir_name.lower()}/{file_name}")
        self.parent.project_tree.refresh(self.parent.project_name)

    def get_project_from_filesystem(self):
        """
        Getter
        :return: the project description
        """
        try:
            project_file = self.conf.projects_directory + self.parent.project_name + "/project.json"
            project_file = open(project_file, "r")
            return json.load(project_file)
        except FileNotFoundError:
            return None
