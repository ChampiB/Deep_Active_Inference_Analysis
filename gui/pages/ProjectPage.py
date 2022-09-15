import os
import tkinter as tk
from tkinter import ttk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.frames.TopBarFrame import TopBarFrame
from gui.widgets.frames.ProjectTreeFrame import ProjectTreeFrame


class ProjectPage(tk.Frame):
    """
    The page used to display a project
    """

    def __init__(self, parent):
        """
        Create the project page
        :param parent: the parent widget, i.e., the analysis window
        """
        # Call parent constructor
        super().__init__(parent)

        # Store config and window
        self.conf = AnalysisConfig.instance
        self.window = parent

        # Change the background color
        self.configure(background=self.conf.colors["dark_gray"])
        self.grid_columnconfigure(0, weight=8)
        self.grid_columnconfigure(1, weight=20)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=400)

        # The current project being displayed
        self.project_name = 'Project Name'
        self.project_description = 'The description of the project'

        # Create the top bar
        self.top_bar = TopBarFrame(self)
        self.top_bar.pack(fill="both")

        self.style = ttk.Style()
        self.style.configure("TSeparator", background=self.conf.colors["blue"], borderwidth=4)
        self.separator = ttk.Separator(self, orient='horizontal', style="TSeparator")
        self.separator.pack(fill="both")

        # Create the main window
        self.project_frame = tk.Frame(self, background=self.conf.colors["dark_gray"])
        self.project_frame.pack(fill="both", expand=True)

        self.project_window = tk.PanedWindow(
            self.project_frame, orient="horizontal", borderwidth=0, background=self.conf.colors["dark_gray"]
        )
        self.project_tree = ProjectTreeFrame(self.project_window)
        self.information = tk.Frame(self.project_window, background=self.conf.colors["dark_gray"])

        self.project_window.add(self.project_tree, minsize=30)
        self.project_window.add(self.information, minsize=30)
        self.project_window.pack(fill="both", expand=True)

        # Frame system
        self.frames_class = self.conf.get_all_classes(self.conf.frames_directory, "gui.widgets.frames.")
        self.frames = {}
        self.current_frame = None

    def show_frame(self, frame_name):
        """
        Show the frame corresponding to the name passed as parameters
        :param frame_name: the name of the page to display
        """
        # Construct the frame if it does not already exist
        if frame_name not in self.frames.keys():
            self.frames[frame_name] = self.frames_class[frame_name](parent=self.information)

        # Hide the currently displayed page
        if self.current_frame is not None:
            self.current_frame.pack_forget()

        # Display the requested page
        self.current_frame = self.frames[frame_name]
        self.current_frame.pack(side="top", fill="both", expand=True)
        self.current_frame.refresh()
        self.current_frame.tkraise()

    def create_new_project(self):
        """
        Create a new project on the file system
        :return: the nane of the newly created project
        """
        # Get the project directory
        projects_directory = self.conf.projects_directory

        # Find a name that is not yet used
        default_name = "New_project_"
        index = -1
        used = True
        while used:
            index += 1
            used = False
            for entry in os.listdir(projects_directory):
                if entry == default_name + str(index):
                    used = True
                    break
        default_name += str(index)

        # Create the project initial folders
        project_dir = projects_directory + default_name
        os.mkdir(project_dir)
        os.mkdir(project_dir + "/agents")
        os.mkdir(project_dir + "/environments")

        return default_name

    def refresh(self, project=None):
        """
        Refresh the page
        :param project: the name of the project to load and display
        """
        if project is None:
            # Create a new project
            project = self.create_new_project()
            description = ""
        else:
            # Load project description
            try:
                description_file = self.conf.projects_directory + project + "/description.txt"
                file = open(description_file, "r+")
                description = "\n".join(file.readlines())
            except OSError:
                description = ""

        # Update project name
        self.project_name = project
        self.top_bar.refresh(project, description)
        self.tkraise()

        # Update project structure
        self.project_tree.refresh(project)
