from math import nan
import matplotlib.pyplot as plt
import pandas as pd
from pandas.errors import EmptyDataError
import json
import tkinter as tk
from gui.DataStorage import DataStorage
from gui.jobs.Job import Job
from gui.widgets.modern.LabelFactory import LabelFactory
from gui.widgets.modern.PolicyDisplay import PolicyDisplay
from gui.widgets.modern.ReconstructionDisplay import ReconstructionDisplay
from gui.widgets.modern.Scrollbar import Scrollbar
from gui.widgets.modern.Slider import Slider
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
        self.canvas_frame.rowconfigure(1, weight=1)
        self.canvas_frame_window = self.canvas.create_window(0, 0, window=self.canvas_frame, anchor='nw')
        for i in range(2):
            self.canvas_frame.columnconfigure(i, weight=1, uniform="true")

        # Display the jobs
        self.images = []
        self.current_row = 0
        color = 'white'
        plt.rcParams['text.color'] = color
        plt.rcParams['axes.labelcolor'] = color
        plt.rcParams['xtick.color'] = color
        plt.rcParams['ytick.color'] = color
        plt.rcParams['legend.frameon'] = 'False'
        self.policy_display = PolicyDisplay(self.canvas_frame)
        self.reconstruction_display = ReconstructionDisplay(self.canvas_frame)
        self.slider = Slider(self.canvas_frame, [self.policy_display, self.reconstruction_display], height=35)
        self.display_analysis(agents, environments)

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
            if job_json is not None:
                self.retrieve_analysis_files(job_json)

        # Display jobs analysis
        self.is_data_missing = True
        self.display_quantitative_metrics(jobs_json)
        self.update_scrollbar()
        self.display_qualitative_metrics(jobs_json)
        self.update_scrollbar()
        if self.is_data_missing:
            label = LabelFactory.create(
                self.canvas_frame, text="No data is currently available...", theme="dark", font_size=14
            )
            padding = self.winfo_height()
            label.grid(row=0, column=0, columnspan=2, pady=max(padding / 2, 25), sticky="nsew")
        self.grid_remove_if_empty()

    def grid_remove_if_empty(self):
        """
        Call grid forget if reconstruction and/or policy display are empty
        """
        if self.reconstruction_display.empty:
            self.reconstruction_display.grid_remove()
        if self.policy_display.empty:
            self.policy_display.grid_remove()
        self.update_scrollbar()

    def display_quantitative_metrics(self, jobs_json):
        """
        Display quantitative metrics
        :param jobs_json: the json of the jobs whose metrics should be displayed
        """
        # Collect the variational free energy and reward
        vfe = {}
        reward = {}
        every_n_rows = 1
        for job_json in jobs_json:
            if job_json is None:
                continue
            env = job_json['env'].replace('_', '/').replace('.json', '')
            agent = job_json['agent'].replace('.json', '')
            try:
                df = pd.read_csv(f"{self.conf.logging_directory}/{env}/{agent}/results.csv")
            except (FileNotFoundError, EmptyDataError) as e:
                print(e)
                continue
            n_rows = int(len(df.index) / 400)
            if n_rows > every_n_rows:
                every_n_rows = n_rows
            if job_json["env"] not in vfe.keys():
                vfe[job_json["env"]] = {}
            vfe[job_json["env"]][job_json["agent"]] = df["loss"]
            if job_json["env"] not in reward.keys():
                reward[job_json["env"]] = {}
            reward[job_json["env"]][job_json["agent"]] = df["reward"]

        # Only keep relevant rows
        for env, agents in vfe.items():
            for agent, df in agents.items():
                vfe[env][agent] = df.iloc[::every_n_rows].head(400)
        for env, agents in reward.items():
            for agent, df in agents.items():
                reward[env][agent] = df.iloc[::every_n_rows].head(400)

        # Draw variational free energy and reward
        self.display_variational_free_energy(every_n_rows, vfe)
        self.current_row = 0
        self.display_reward(every_n_rows, reward)

    def display_reward(self, every_n_rows, reward):
        """
        Display the reward gathered by the agent
        :param every_n_rows: the number of rows (time steps) between two VFE values
        :param reward: the reward values
        """
        xs = [every_n_rows * i for i in range(400)]
        image_file = f"{self.conf.data_directory}/saved_figure.png"
        for env, agents in reward.items():
            plt.clf()
            for agent, ys in agents.items():
                ys = ys if len(ys) == 400 else pd.concat([ys, pd.Series([nan] * (400 - len(ys)))])
                plt.plot(xs, ys, label=agent)
            plt.xlabel("Training Iterations")
            plt.ylabel("Rewards")
            plt.title(f"Rewards on {env.replace('.json', '')} environments")
            plt.legend()
            plt.savefig(image_file, transparent=True)
            photo = ImageTk.PhotoImage(Image.open(image_file))
            label = LabelFactory.create(self.canvas_frame, image=photo, theme="dark")
            label.grid(row=self.current_row, column=1, pady=5, sticky="nsew")
            self.is_data_missing = False
            self.current_row += 1
            self.images.append(photo)

    def display_variational_free_energy(self, every_n_rows, vfe):
        """
        Display the variational free energy
        :param every_n_rows: the number of rows (time steps) between two VFE values
        :param vfe: the variational free energy values
        """
        xs = [every_n_rows * i for i in range(400)]
        image_file = f"{self.conf.data_directory}/saved_figure.png"
        for env, agents in vfe.items():
            plt.clf()
            for agent, ys in agents.items():
                ys = ys if len(ys) == 400 else pd.concat([ys, pd.Series([nan] * (400 - len(ys)))])
                plt.plot(xs, ys, label=agent)
            plt.xlabel("Training Iterations")
            plt.ylabel("Variational Free Energy")
            plt.title(f"Variational free energy on {env.replace('.json', '')} environments")
            plt.legend()
            plt.savefig(image_file, transparent=True)
            photo = ImageTk.PhotoImage(Image.open(image_file))
            label = LabelFactory.create(self.canvas_frame, image=photo, theme="dark")
            label.grid(row=self.current_row, column=0, pady=5, sticky="nsew")
            self.is_data_missing = False
            self.current_row += 1
            self.images.append(photo)

    def display_qualitative_metrics(self, jobs_json):
        """
        Display the policy taken by the agent and the reconstructed images if the agent is model based
        :param jobs_json: the json of the jobs whose metrics should be displayed
        """
        # Position widget on the screen
        self.slider.grid(row=self.current_row, column=0, columnspan=2, sticky='new', pady=10)
        self.current_row += 1
        self.policy_display.grid(row=self.current_row, column=0, columnspan=2, sticky='new', pady=10)
        self.current_row += 1
        self.reconstruction_display.grid(row=self.current_row, column=0, columnspan=2, sticky='new', pady=10)
        self.current_row += 1

        # Update jobs
        self.policy_display.set_jobs(jobs_json)
        self.reconstruction_display.set_jobs(jobs_json)

        # Get slider's value and display corresponding images
        value = self.slider.get()
        if self.policy_display.set_value(value) is False:
            self.is_data_missing = False
        if self.reconstruction_display.set_value(value) is False:
            self.is_data_missing = False
        if self.is_data_missing:
            self.slider.grid_remove()

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
        self.policy_display.stop()
