import json
import os
import time

from git import Repo
from threading import Thread
from gui.AnalysisConfig import AnalysisConfig
from hosts.HostInterface import HostInterface
from paramiko import SSHClient, AutoAddPolicy


class ServerSSH(HostInterface):
    """
    A class representing an ssh server (with slurm installed)
    """

    def __init__(self, server_name, username, hostname, repository_path, **kwargs):
        """
        Constructor
        :param server_name: the server name
        :param username: the username to use when login to the ssh server
        :param hostname: the hostname of the ssh server
        :param repository_path: the path to the repository on the server
        :param kwargs: the remaining arguments
        """
        self.conf = AnalysisConfig.instance
        self.server_name = server_name
        self.username = username
        self.hostname = hostname
        self.repository_path = repository_path
        if self.repository_path[-1] != "/":
            self.repository_path += "/"
        self.locked = False

    def update_repository(self):
        """
        Make sure the remote repository is up-to-date
        """
        try:
            repo = Repo(self.conf.root_directory)
            repo.git.add(all=True)
            repo.index.commit("update the agents and environments")
            origin = repo.remote(name='origin')
            origin.push()
        except Exception as e:
            print(e)

    def setup_ssh_server(self, client):
        """
        Set up the ssh server
        :param client: the client to the server
        """
        # Clone the repository, if the directory does not already exist
        path, repository_name = os.path.split(self.repository_path[:-1])
        self.execute(
            client,
            f"[ ! -d '{self.repository_path}' ] &&"
            f"cd {path} &&"
            "git clone https://github.com/ChampiB/Deep_Active_Inference_Analysis.git"
        )

        # Make sure the repository is up to day
        self.execute(
            client,
            f"cd {self.repository_path} &&"
            f"git add . &&"
            f"git commit -m 'tmp' &&"
            f"git pull"
        )

        # Create the virtual environment, if the directory does not exist
        self.execute(
            client,
            f"python3 -m venv {self.repository_path}/venv"
        )

        # Activate environment and install requirements
        self.execute(
            client,
            f"cd {self.repository_path} &&"
            f"source '{self.repository_path}/venv/bin/activate' &&"
            f"pip install -r requirements.txt"
        )

    def run_task(self, agent, env, project_name):
        """
        Run the next task in the queue
        :param agent: the agent
        :param env: the environment
        :param project_name: the name of the project for which the agent is trained
        """
        while self.locked:
            time.sleep(0.5)
        self.locked = True

        # Save agent and environment names
        agent_name = agent
        env_name = env

        # Update the repository
        self.update_repository()

        # Open SSH connection
        client = SSHClient()
        client.load_host_keys(self.conf.ssh_key_directory + "known_hosts")
        client.load_system_host_keys()
        client.set_missing_host_key_policy(AutoAddPolicy())
        client.connect(hostname=self.hostname, username=self.username, port=22)

        # Check if job should be re-run
        json_path = self.get_job_json_path(agent, env, project_name)
        if os.path.exists(json_path):
            job = json.load(open(json_path, "r"))
            values = self.execute(client, f"squeue | grep {job['job_id']}", return_stdout=True)
            if len(values["stdout"]) != 0:
                print(f"Job {job['job_id']} is still running.")
                self.locked = False
                return
            values = self.execute(
                client,
                f"cat {self.repository_path}slurm-{job['job_id']}.out | grep 'Agent trained successfully!'",
                return_stdout=True
            )
            if len(values["stdout"]) != 0:
                print(f"Job {job['job_id']} finished successfully.")
                self.locked = False
                return

        # Start the job
        self.setup_ssh_server(client)
        project_dir = self.repository_path + f"data/projects/{project_name}/"
        agent = project_dir + f"agents/{agent}"
        env = project_dir + f"environments/{env}"
        training_script = f"{self.repository_path}train_agent.sh {self.repository_path}"
        values = self.execute(
            client, f"cd {self.repository_path} &&"
            f"source '{self.repository_path}/venv/bin/activate' &&"
            f"sbatch -p gpu --mem=10G --gres-flags=disable-binding --gres=gpu {training_script} \"{agent}\" \"{env}\"",
            return_stdout=True
        )
        print(
            f"cd {self.repository_path} &&"
            f"source '{self.repository_path}/venv/bin/activate' &&"
            f"sbatch -p gpu --mem=10G --gres-flags=disable-binding --gres=gpu {training_script} \"{agent}\" \"{env}\""
        )

        # Save job in file
        job_id = values["stdout"][0].split(" ")[-1]
        try:
            job_id = int(job_id)
        except Exception as e:
            print(e)
        file = open(json_path, mode="w+")
        json.dump({
            "agent": agent_name,
            "env": env_name,
            "status": "pending",
            "host": self.server_name,
            "hardware": "gpu",
            "job_id": job_id
        }, file, indent=2)

        # Close client
        client.close()
        self.locked = False

    @staticmethod
    def refresh_job(job_json, project_name):
        """
        Refresh the job by querying the ssh server
        :param job_json: the job json
        :param project_name: the project name of the job
        :return: the updated job json
        """
        # Get host
        conf = AnalysisConfig.instance
        host = conf.servers[job_json["host"]]

        # Open SSH connection
        client = SSHClient()
        client.load_host_keys(conf.ssh_key_directory + "known_hosts")
        client.load_system_host_keys()
        client.set_missing_host_key_policy(AutoAddPolicy())
        client.connect(hostname=host["hostname"], username=host["username"], port=22)

        # Update job json
        values = ServerSSH.execute(client, f"squeue | grep {job_json['job_id']}", return_stdout=True)
        if len(values["stdout"]) != 0:
            squeue_info = values["stdout"][0].split()
            job_json["status"] = f"running[{squeue_info[5]}]" if squeue_info[4] == "R" else "pending"
        else:
            values = ServerSSH.execute(
                client,
                f"cat {host['repository_path']}/slurm-{job_json['job_id']}.out | grep 'Agent trained successfully!'",
                return_stdout=True
            )
            job_json["status"] = "success" if len(values["stdout"]) != 0 else "crashed"

        values = ServerSSH.execute(
            client,
            f"cat {host['repository_path']}/slurm-{job_json['job_id']}.out | grep 'GPU:'",
            return_stdout=True
        )
        job_json["hardware"] = values["stdout"][0].split(" ")[1] if len(values["stdout"]) != 0 else "gpu"

        # Save job on filesystem
        json_path = HostInterface.get_job_json_path(job_json["agent"], job_json["env"], project_name)
        file = open(json_path, mode="w")
        json.dump(job_json, file, indent=2)
        return job_json

    @staticmethod
    def execute(client, command, return_stdout=False):
        """
        Execute a command and close all channel returned by the command call
        :param client: the client that must be used to run the command
        :param command: the command
        :param return_stdout: whether to return the content of stdout
        """
        values = {}
        stdin, stdout, stderr = client.exec_command(command)
        if return_stdout:
            values["stdout"] = stdout.readlines()
        stdin.close()
        stdout.close()
        stderr.close()
        return values

    def train(self, agent, env, project_name):
        """
        Train the agent in the environment
        :param agent: the agent
        :param env: the environment
        :param project_name: the name of the project for which the agent is trained
        """
        Thread(target=self.run_task, args=(agent, env, project_name)).start()
