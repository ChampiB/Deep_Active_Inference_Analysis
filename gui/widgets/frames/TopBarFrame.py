import os
import tkinter as tk
from gui.AnalysisAssets import AnalysisAssets
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.frames.EmptyFrame import EmptyFrame
from gui.widgets.frames.ProjectRenamingFrame import ProjectRenamingFrame
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.ToolTip import ToolTip


class TopBarFrame(tk.Frame):
    """
    A class representing the top bar of the analysis tool
    """

    def __init__(
        self, parent, display_delete_button=True, display_project_name=True, display_run_button=True,
        display_analysis_button=True, command="go_to_project_selection_page"
    ):
        """
        Constructor
        :param parent: the parent widget
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
            self.name_label.grid(row=0, column=col_index, padx=6, pady=6)
            col_index += 1

        # Add the run button
        self.training_location = "locally"
        if display_run_button:
            self.run_button = ButtonFactory.create(self, image=self.assets.get("run_button"))
            self.run_button.grid(row=0, column=col_index, padx=3, pady=3, ipadx=6, ipady=3)
            self.run_button_tip = ToolTip(self.run_button, f"Run training '{self.training_location}'")
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

        # Frame for renaming the project
        self.project_renaming_frame = None

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
            self.project_renaming_frame = ProjectRenamingFrame(self.parent)

    def refresh(self, project):
        """
        Refresh the top bar of the analysis tool
        :param project: the project name to display
        """
        self.name_label.config(text=project)

    def delete_selection(self):
        """
        Delete the selected agents and environments
        """
        for dir_name, file_name in self.parent.project_tree.selected_entries:
            os.remove(self.conf.projects_directory + f"{self.parent.project_name}/{dir_name.lower()}/{file_name}")
        self.parent.project_tree.refresh(self.parent.project_name)
