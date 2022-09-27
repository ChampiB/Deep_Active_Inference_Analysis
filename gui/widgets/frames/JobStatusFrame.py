import json
import os
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from gui.DataStorage import DataStorage
from gui.json.Job import Job
from gui.widgets.modern.ButtonFactory import ButtonFactory
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.Scrollbar import Scrollbar
from hosts.impl.ServerSSH import ServerSSH


class JobStatusFrame(tk.Frame):
    """
    A class displaying the job status
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

        # Load delete button image
        self.delete_button_img = self.assets.get("red_delete_button")

        # Change background color and configure AgentFrame
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
        threading.Thread(target=self.display_jobs, args=(agents, environments)).start()

        self.scrollbar.bind_wheel(self, recursive=True)
        self.agent_form = None
        self.canvas.bind('<Configure>', self.frame_width)

    def display_jobs(self, agents, environments):
        """
        Display existing jobs
        :param agents: the agents whose jobs should be displayed
        :param environments: the environments whose jobs should be displayed
        """
        # Create header
        for i, text in enumerate(["Agent", "Environment", "Status[dd:hh:mm:ss]", "Host", "Hardware", ""]):
            label = LabelFactory.create(self.canvas_frame, text=text, theme="dark", font_size=14)
            label.grid(row=0, column=i, pady=5, sticky="nsew")
        separator = ttk.Separator(self.canvas_frame, orient='horizontal')
        separator.grid(row=1, column=0, columnspan=5, sticky="nsew")

        # Create table's rows
        row_index = 2
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

        # Display jobs
        for job_json in jobs_json:
            if job_json is None:
                continue
            self.display_job(row_index, job_json)
            row_index += 1
            self.scrollbar.bind_wheel(self, recursive=True)
            self.refresh()

    def display_job(self, row_index, job_json):
        """
        Display one job
        :param row_index: the index of the row where the job should be displayed
        :param job_json: the path to the json describing the job
        """
        # Create one table row
        bg = self.conf.colors["dark_gray"] if row_index % 2 != 0 else self.conf.colors["gray"]
        row = tk.Frame(self.canvas_frame, bg=bg)
        for i in range(5):
            row.columnconfigure(i, weight=1, uniform="true")
            row.columnconfigure(i, weight=1, uniform="true")
        row.grid(row=row_index, column=0, columnspan=5, sticky="nsew")

        # Update job if it is running on the server
        if "job_id" in job_json.keys():
            job_json = ServerSSH.refresh_job(job_json, self.project_page.project_name)

        # Create row's columns
        for i, key in enumerate(["agent", "env", "status", "host", "hardware"]):
            text = job_json[key].replace(".json", "")
            if key == "status" and text == "running":
                if "execution_time" in job_json.keys():
                    text += "[" + job_json["execution_time"] + "]"
                else:
                    start_time = datetime.strptime(job_json["start_time"], "%m/%d/%Y, %H:%M:%S")
                    execution_time = self.get_execution_time(start_time, datetime.now())
                    text += "[" + execution_time + "]"

            theme = "dark" if row_index % 2 != 0 else "gray"
            label = LabelFactory.create(row, text=text, theme=theme)
            i_pad_y = 5 if row_index % 2 != 0 else 4
            label.grid(row=0, column=i, pady=5, ipady=i_pad_y, sticky="nsew")

        theme = "dark" if row_index % 2 != 0 else "light"
        button = ButtonFactory.create(
            row, image=self.delete_button_img, theme=theme, command=lambda j=job_json: self.delete_job(j)
        )
        button.grid(row=0, column=5, pady=5, ipadx=5, ipady=5, sticky="nsew")

    def delete_job(self, job_json):
        """
        Delete the job described by the json
        :param job_json: the json
        """
        # Delete job file
        project_name = self.project_page.project_name
        json_path = Job.get_json_path(job_json["agent"], job_json["env"], project_name)
        if os.path.exists(json_path):
            os.remove(json_path)

        # Cancel job on cluster
        if "job_id" in job_json.keys():
            if job_json["status"] == "pending" or job_json["status"].startwith("running"):
                ServerSSH(**job_json).cancel_job(job_json["job_id"])

        # Remove logging directory
        # if "job_id" not in job_json.keys():
            # TODO remove logging is local

        self.project_page.show_frame("JobStatusFrame", {"agents": self.agents, "environments": self.environments})

    @staticmethod
    def get_execution_time(start_time, end_time):
        """
        Compute the execution time
        :param start_time: the starting time
        :param end_time: the ending time
        :return: the execution time as a string
        """
        execution_time = end_time - start_time
        duration_in_s = execution_time.total_seconds()
        days = divmod(duration_in_s, 86400)
        hours = divmod(days[1], 3600)
        minutes = divmod(hours[1], 60)
        seconds = divmod(minutes[1], 1)
        execution_time = f"{int(minutes[0]):02}:{int(seconds[0]):02}"
        if hours[0] != 0 or days[0] != 0:
            execution_time = f"{int(hours[0])}:02:{execution_time}"
        if days[0] != 0:
            execution_time = f"{int(days[0])}:{execution_time}"
        return execution_time

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
