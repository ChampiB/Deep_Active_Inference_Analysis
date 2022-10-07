import json
import os
import shutil
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from gui.DataStorage import DataStorage
from gui.jobs.Job import Job
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.Scrollbar import Scrollbar
from hosts.impl.ServerSSH import ServerSSH


class AnalysisFrame(tk.Frame):
    """
    A class displaying the job analysis
    Only the job corresponding to the agent-environment pairs provided by the user will be displayed
    """

    def __init__(self, parent, agents=None, environments=None, **kwargs):
        """
        Constructor
        :param parent: parent widget
        :param agents: the agents whose jobs should be displayed
        :param environments: the environments whose jobs should be displayed
        :param kwargs: the remaining arguments
        """

        # Call parent constructor
        super().__init__(parent)

        # Save parameters passed as input
        self.parent = parent
        self.project_page = parent.master.master.master
        self.conf = DataStorage.get("conf")
        self.window = DataStorage.get("window")
        self.assets = DataStorage.get("assets")
        self.agents = agents
        self.environments = environments

        # Change background color and configure AnalysisFrame
        self.config(background=self.conf.colors["dark_gray"])
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=120)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        # Create the canvas and scrollbar
        self.canvas = tk.Canvas(self, bg=self.conf.colors["dark_gray"], highlightthickness=0)
        self.canvas.grid(row=0, column=1, sticky="news")
        self.scrollbar = Scrollbar(self, command=self.canvas.yview)
        self.scrollbar.grid(row=0, column=2, sticky='nes')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Create the canvas frame
        self.canvas_frame = tk.Frame(self.canvas, background=self.conf.colors["dark_gray"])
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas_frame.rowconfigure(1, weight=1)
        self.canvas_frame_window = self.canvas.create_window(0, 0, window=self.canvas_frame, anchor='nw')
        for i in range(5):
            self.canvas_frame.columnconfigure(i, weight=1, uniform="true")

        # Display the jobs
        threading.Thread(target=self.display_analysis, args=(agents, environments)).start()

        self.scrollbar.bind_wheel(self, recursive=True)
        self.canvas.bind('<Configure>', self.frame_width)

    def display_analysis(self, agents, environments):
        """
        Display the analysis of existing jobs
        :param agents: the agents whose analysis should be displayed
        :param environments: the environments whose analysis should be displayed
        """
        # Get jobs whose analysis must be displayed
        project_name = self.project_page.project_name
        if agents is None or environments is None:
            # Get all jobs
            jobs_directory = self.conf.projects_directory + self.project_page.project_name + "/jobs/"
            jobs = self.conf.get_all_files(jobs_directory)
            self.window.filesystem_mutex.acquire()
            jobs_json = [json.load(open(jobs_directory + job, "r")) for job in jobs]
            self.window.filesystem_mutex.release()
        else:
            # Get selected jobs
            mutex = self.window.filesystem_mutex
            jobs_json = [Job(mutex, agent, env, project_name).json for agent in agents for env in environments]

        # Retrieve the analysis files
        for job_json in jobs_json:
            self.get_relevant_files(job_json)

        # Display jobs analysis
        self.display_quantitative_metrics()
        self.update_scrollbar()
        self.display_qualitative_metrics()
        self.update_scrollbar()

    def display_quantitative_metrics(self):
        pass

    def display_qualitative_metrics(self):
        pass

    def get_relevant_files(self, job_json):
        # Get the host
        # TODO get job's host
        server_name = self.server_combobox.get()

        host_json = self.conf.servers[server_name]
        host_json["server_name"] = server_name
        host = HostFactory.create(host_json["class"], host_json)

        # TODO retrieve files
        # Train the agents on the environment
        for agent in agents:
            for env in environments:
                host.train(agent, env, self.parent.project_name)

    def update_scrollbar(self):
        """
        Update the scrollbar
        """
        self.scrollbar.bind_wheel(self, recursive=True)
        self.refresh()

    def frame_width(self, event):
        """
        Configure the canvas frame width
        :param event: the event that triggered the call to this function
        """
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame_window, width=canvas_width)

    def refresh(self):
        """
        Refresh the new agent frame
        """
        # Update agent form idle tasks to let tkinter calculate buttons sizes
        self.canvas_frame.update_idletasks()

        # Set the canvas scrolling region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def stop(self):
        """
        Stop all tasks running in background
        """
        pass
