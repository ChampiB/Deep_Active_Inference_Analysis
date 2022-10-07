import matplotlib.pyplot as plt
import pandas as pd
import json
import threading
import tkinter as tk
from gui.DataStorage import DataStorage
from gui.jobs.Job import Job
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.Scrollbar import Scrollbar
from hosts.HostFactory import HostFactory
from PIL import Image, ImageTk


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

        # Boolean to check whether data is available
        self.is_data_missing = True

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
        self.images = []
        self.current_row = 0
        self.current_column = 1
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
            self.retrieve_analysis_files(job_json)

        # Display jobs analysis
        self.is_data_missing = True
        self.display_quantitative_metrics(jobs_json)
        self.update_scrollbar()
        self.display_qualitative_metrics()
        self.update_scrollbar()
        if self.is_data_missing:
            label = LabelFactory.create(
                self.canvas_frame, text="No data is currently available...", theme="dark", font_size=14
            )
            padding = self.winfo_height()
            label.grid(row=1, column=1, columnspan=3, pady=padding / 2, sticky="nsew")

    def display_quantitative_metrics(self, jobs_json):
        """
        Display quantitative metrics
        :param jobs_json: the json of the jobs whose metrics should be displayed
        """
        # Collect the variational free energy and reward
        vfe = {}
        reward = {}
        every_n_rows = 0
        for job_json in jobs_json:
            env = job_json['env'].replace('_', '/').replace('.json', '')
            agent = job_json['agent'].replace('.json', '')
            df = pd.read_csv(f"{self.conf.logging_directory}/{env}/{agent}/results.csv")
            n_rows = len(df.index) / 400
            if n_rows > every_n_rows:
                every_n_rows = n_rows
            print(every_n_rows)
            print(df.index)
            if job_json["env"] not in vfe.keys():
                vfe[job_json["env"]] = {}
            vfe[job_json["env"]][job_json["agent"]] = df["loss"]
            if job_json["env"] not in reward.keys():
                reward[job_json["env"]] = {}
            reward[job_json["env"]][job_json["agent"]] = df["reward"]

        # Only keep relevant rows
        for env, agents in reward.items():
            for agent, df in agents.items():
                vfe[env][agent] = df.iloc[::every_n_rows, :]
        for env, agents in reward.items():
            for agent, df in agents.items():
                reward[env][agent] = df.iloc[::every_n_rows, :]

        # Draw variational free energy
        xs = [every_n_rows * i for i in range(400)]
        image_file = f"{self.conf.data_directory}/saved_figure.png"
        for env, agents in vfe.items():
            plt.clf()
            for agent, ys in agents.items():
                plt.plot(xs, ys, label=agent)
            plt.xlabel("Training Iterations")
            plt.ylabel("Variational Free Energy")
            plt.title(f"The agents' variational free energy on {env}")
            plt.legend()
            plt.savefig(image_file, transparent=True)
            photo = ImageTk.PhotoImage(Image.open(image_file))
            label = LabelFactory.create(self.canvas_frame, image=photo, theme="dark", font_size=14)
            label.grid(row=self.current_row, column=self.current_column, columnspan=3, pady=5, sticky="nsew")
            self.current_row += 1
            if self.current_row > 3:
                self.current_row = 1
                self.current_column += 1
            self.images.append(photo)
        # TODO if data_present:
        # TODO     self.is_data_missing = False

    def display_qualitative_metrics(self):
        print("display_qualitative_metrics")
        # if data_present:
        #     self.is_data_missing = False
        # TODO
        pass

    def retrieve_analysis_files(self, job_json):
        """
        Retrieve the files required for the analysis of the job
        :param job_json: the job whose files must be retrieved
        """
        # Get the host
        server_name = job_json["host"]
        host_json = self.conf.servers[server_name]
        host_json["server_name"] = server_name
        host = HostFactory.create(host_json["class"], host_json)

        # Train the agents on the environment
        host.retrieve_analysis_files(job_json)

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
