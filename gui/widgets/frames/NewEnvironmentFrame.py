import os
import tkinter as tk
from tkinter import ttk
from gui.AnalysisConfig import AnalysisConfig
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.Entry import Entry
from gui.widgets.modern.LabelFactory import LabelFactory


class NewEnvironmentFrame(tk.Frame):

    def __init__(self, parent):

        # Call parent constructor
        super().__init__(parent)

        # Save parameters
        self.parent = parent
        self.conf = AnalysisConfig.instance

        # Default project name
        self.default_project_name = "<environment name here>"

        # Place the project renaming frame in the center od the screen
        self.place(relwidth=0.25, relheight=0.175, relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Place the project renaming frame in the center od the screen
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)

        # Change background color
        self.config(background=self.conf.colors["dark_gray"])

        # Add the new project name label
        self.new_project_name_label = LabelFactory.create(self, text="New project name:", theme="dark")
        self.new_project_name_label.grid(row=1, column=0, padx=(10, 0), pady=(5, 10), sticky="nsw")

        # Add the new project name entry
        self.renaming_entry = Entry(self, help_message=self.default_project_name)
        self.renaming_entry.grid(row=1, column=1, columnspan=2, padx=(0, 10), pady=(5, 10), sticky="nsew")
        self.renaming_entry.focus()

        # Add the rename button
        self.rename_button = ButtonFactory.create(self, text="Rename", command=self.change_project_name, theme="blue")
        self.rename_button.grid(row=2, column=1, columnspan=2, pady=10, padx=(0, 10), ipady=10, sticky="nsew")

    def change_project_name(self):
        # Check that the new project name is not empty
        self.renaming_entry.remove_help_message()
        new_project_name = self.renaming_entry.get()
        if new_project_name == "":
            self.place_forget()
            return

        # Change project name
        projects_directory = self.conf.projects_directory
        self.parent.top_bar.name_label.config(text=new_project_name)
        os.rename(projects_directory + self.parent.project_name, projects_directory + new_project_name)
        self.parent.project_name = new_project_name
        self.place_forget()

    def refresh(self):
        pass
