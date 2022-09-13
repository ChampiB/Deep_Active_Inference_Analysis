import shutil
import os
import tkinter as tk
from gui.AnalysisAssets import AnalysisAssets
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.Scrollbar import Scrollbar
from gui.widgets.frames.TopBarFrame import TopBarFrame


class ProjectSelectionPage(tk.Frame):
    """
    The page used to select the project to edit
    """

    def __init__(self, parent):
        """
        Create the project selection page
        :param parent: the parent widget, i.e., the analysis window
        """
        # Call parent constructor
        super().__init__(parent)

        # Store config, assets and window
        self.window = parent
        self.conf = AnalysisConfig.instance
        self.assets = AnalysisAssets.instance

        # Set rows and columns weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=10)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=10)
        self.grid_columnconfigure(2, weight=1)

        # Set background color
        self.configure(background=self.conf.colors["dark_gray"])

        # Create the top bar
        self.top_bar = TopBarFrame(
            self, display_delete_button=False, display_project_name=False, display_run_button=False,
            display_analysis_button=False, command="quit"
        )
        self.top_bar.grid(row=0, column=2, sticky="nsew")

        # Create project selection frame
        self.frame = tk.Frame(self, bg=self.conf.colors["dark_gray"])
        self.frame.grid(row=1, column=1, sticky="nsew")

        # Change the background color
        self.frame.configure(background=self.conf.colors["dark_gray"])
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=5)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=20)

        # Ask the user to select a project
        self.label = LabelFactory.create(self.frame, text="Select a project...", theme="dark", font_size=22)
        self.label.grid(row=0, column=1, sticky='news')

        # Create a frame for the canvas
        self.canvas_frame = tk.Frame(
            self.frame, highlightthickness=2, highlightbackground=self.conf.colors["gray"]
        )
        self.canvas_frame.config(background=self.conf.colors["dark_gray"])
        self.canvas_frame.grid(row=2, column=1, sticky='news')
        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(0, weight=100)
        self.canvas_frame.columnconfigure(1, weight=1)
        self.canvas_frame.grid_propagate(False)

        # Create the canvas
        self.canvas = tk.Canvas(self.canvas_frame, highlightthickness=0, bg=self.conf.colors["dark_gray"])
        self.canvas.grid(row=0, column=0, sticky="news")

        # Link a scrollbar to the canvas
        self.scrollbar = Scrollbar(self.canvas_frame, command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=1, sticky='news', pady=10)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(background=self.conf.colors["dark_gray"])

        # Create a frame containing the buttons
        self.frame_buttons = tk.Frame(self.canvas, bg=self.conf.colors["dark_gray"])
        self.canvas.create_window(0, 0, window=self.frame_buttons, anchor='nw')
        self.scrollbar.bind_wheel(self.frame_buttons)

        self.projects = None
        self.buttons = {}  # {key: (project_button, delete_button)}
        self.refresh()

    def get_project_name(self, index):
        """
        Getter
        :param index: the project's index
        :return: the project name
        """
        return "New Project" if index >= len(self.projects) else self.projects[index]

    def display_projects(self):
        """
        Display the existing project, and the new project button
        """
        index = 0
        for i in range(0, int(len(self.projects) / 3) + 1):
            for j in range(0, 3):
                # Stop the iterations, if no more projects to display
                if index > len(self.projects):
                    break

                # Add project button
                project_button = self.get_project_button(index)
                project_button.grid(row=2 * i, column=j, sticky='news', padx=70, pady=(30, 0))

                # Add delete button
                delete_button = self.get_delete_button(index)
                delete_button.grid(row=2 * i + 1, column=j, sticky='news', padx=70, pady=(0, 30))

                # Store buttons
                key = self.get_project_name(index)
                self.buttons[key] = (project_button, delete_button)

                # Increase index
                index += 1

    def get_project_button(self, index):
        """
        Getter
        :param index: the project index of the button that must be returned
        :return: the button
        """
        # Return button if already exist
        text = self.get_project_name(index)
        if text in self.buttons.keys():
            return self.buttons[text][0]

        # Create the button
        page_name = "ProjectPage"
        if index == len(self.projects):
            button = ButtonFactory.create(
                self.frame_buttons, image=self.assets.get("new_button"), text=text,
                command=lambda n=page_name: self.window.show_page(n, {}), theme="blue"
            )
        else:
            button = ButtonFactory.create(
                self.frame_buttons, theme="blue",
                image=self.assets.get("existing_project_button"), text=self.truncate(text, 20),
                command=lambda n=page_name: self.window.show_page(n, {"project": self.projects[index]})
            )
        self.scrollbar.bind_wheel(button)
        return button

    def get_delete_button(self, index):
        """
        Getter
        :param index: the project index of the button that must be returned
        :return: the button
        """
        # Return button if already exist
        text = self.get_project_name(index)
        if text in self.buttons.keys():
            return self.buttons[text][1]

        # Create the button
        if index == len(self.projects):
            button = ButtonFactory.create(self.frame_buttons, theme="invisible_dark")
            self.scrollbar.bind_wheel(button)
            return button

        button = ButtonFactory.create(
            self.frame_buttons, image=self.assets.get("delete_button"), theme="red",
            command=lambda i=index: self.delete_project(self.projects[i])
        )
        self.scrollbar.bind_wheel(button)
        return button

    def delete_project(self, project_name):
        """
        Delete the project whose name is passed as parameters
        :param project_name: the project name
        """
        shutil.rmtree(self.conf.projects_directory + project_name)
        self.refresh()

    @staticmethod
    def truncate(string, max_len):
        """
        Truncate the string if its length is superior to the maximum length
        :param string: the string
        :param max_len: the maximum length
        :return: the truncated string
        """
        if len(string) > max_len:
            return string[0: max_len-3] + "..."
        return string

    def refresh(self):
        """
        Refresh the page
        """
        # Load all projects
        self.projects = self.conf.get_all_directories(self.conf.projects_directory)

        # Clear old buttons, and
        key_to_delete = []
        for key, (project_button, delete_button) in self.buttons.items():
            if key not in self.projects:
                project_button.grid_forget()
                delete_button.grid_forget()
                key_to_delete.append(key)
        for key in key_to_delete:
            del self.buttons[key]

        # Display the projects
        self.display_projects()

        # Update buttons frames idle tasks to let tkinter calculate buttons sizes
        self.frame_buttons.update_idletasks()

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
