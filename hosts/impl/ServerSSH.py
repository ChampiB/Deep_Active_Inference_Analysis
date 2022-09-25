import os
from threading import Thread
from gui.AnalysisConfig import AnalysisConfig
from hosts.HostInterface import HostInterface
from paramiko import SSHClient, AutoAddPolicy


class ServerSSH(HostInterface):
    """
    A class representing an ssh server (with slurm installed)
    """

    def __init__(self, username, hostname, repository_path, **kwargs):
        """
        Constructor
        :param username: the username to use when login to the ssh server
        :param hostname: the hostname of the ssh server
        :param repository_path: the path to the repository on the server
        :param kwargs: the remaining arguments
        """
        self.conf = AnalysisConfig.instance
        self.username = username
        self.hostname = hostname
        self.repository_path = repository_path
        if self.repository_path[-1] != "/":
            self.repository_path += "/"

    def run_task(self, agent, env, project_name):
        """
        Run the next task in the queue
        :param agent: the agent
        :param env: the environment
        :param project_name: the name of the project for which the agent is trained
        """
        # Update the repository
        os.system('git add .')
        os.system('git commit -m "update the agents and environments"')
        os.system('git push')

        # Open SSH connection
        client = SSHClient()
        client.load_host_keys(self.conf.ssh_key_directory + "known_hosts")
        client.load_system_host_keys()
        client.set_missing_host_key_policy(AutoAddPolicy())
        client.connect(hostname=self.hostname, username=self.username, port=22)

        # Clone the repository, if the directory does not already exist
        path, repository_name = os.path.split(self.repository_path[:-1])
        cmd = f"[ ! -d '{self.repository_path}' ] && cd {path} && " \
            + "git clone https://github.com/ChampiB/Deep_Active_Inference_Analysis.git"
        self.execute(client, cmd)

        # Make sure the repository is up to day
        self.execute(client, f"cd {self.repository_path} && git pull")

        # Create the virtual environment, if the directory does not exist
        self.execute(client, f"[ ! -d '{self.repository_path}/venv' ] && python3 -m venv {self.repository_path}/venv")

        # Activate environment and install requirements
        self.execute(
            client,
            f"cd {self.repository_path} && "
            f"source '{self.repository_path}/venv/bin/activate' && "
            f"pip install -r requirements.txt"
        )

        # Start the job
        project_dir = self.repository_path + f"data/projects/{project_name}/"
        agent = project_dir + f"agents/{agent}"
        env = project_dir + f"environments/{env}"
        print(f"{agent} {env}")
        training_script = f"{self.repository_path}train_agent.sh"
        self.execute(
            client, f"cd {self.repository_path} && "
            f"source '{self.repository_path}/venv/bin/activate' && "
            f"sbatch -p gpu --mem=10G --gres-flags=disable-binding --gres=gpu {training_script} {agent} {env}"
        )

        # Close client
        client.close()

    @staticmethod
    def execute(client, command):
        """
        Execute a command and close all channel returned by the command call
        :param client: the client that must be used to run the command
        :param command: the command
        """
        stdin, stdout, stderr = client.exec_command(command)
        print(command)
        print(stderr.readlines())
        print()
        stdin.close()
        stdout.close()
        stderr.close()

    def train(self, agent, env, project_name):
        """
        Train the agent in the environment
        :param agent: the agent
        :param env: the environment
        :param project_name: the name of the project for which the agent is trained
        """
        Thread(target=self.run_task, args=(agent, env, project_name)).start()
