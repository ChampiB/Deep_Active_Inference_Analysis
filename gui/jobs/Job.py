import hashlib
import json
import os
import sys
from datetime import datetime
import train_agent
from gui.AnalysisConfig import AnalysisConfig


class Job:
    """
    A class representing a job
    """

    def __init__(self, mutex, agent, env, project_name):
        """
        Constructor
        :param mutex: the mutex to lock when accessing the file system
        :param agent: the job's agent
        :param env: the job's environment
        :param project_name: the name of the project running the job
        """
        # Store the mutex
        self.mutex = mutex

        # Pre-process parameters
        agent = agent.split("/")[-1]
        env = env.split("/")[-1]

        # Load job from file system
        self.json_path = Job.get_json_path(agent, env, project_name)
        self.mutex_lock()
        try:
            if not os.path.exists(self.json_path):
                raise Exception()
            with open(self.json_path, "r") as file:
                self.json = json.load(file)
        except Exception as e:
            print(e)
            self.json = None
        self.mutex_unlock()

    def mutex_lock(self):
        """
        Safely acquire the mutex
        """
        if self.mutex is not None:
            self.mutex.acquire()

    def mutex_unlock(self):
        """
        Safely release the mutex
        """
        if self.mutex is not None:
            self.mutex.release()

    def update(self, key, value, save=True):
        """
        Update one of the job key-value pair
        :param key: the key
        :param value: the value
        :param save: whether to apply change to the file system
        """
        # Pre-processing
        if key == "job_id":
            try:
                value = int(value)
            except Exception as e:
                print(e)

        # Update key-value pair
        self.json[key] = value

        # Save job on filesystem
        if save:
            self.mutex_lock()
            with open(self.json_path, mode="w+") as file:
                json.dump(self.json, file, indent=2)
            self.mutex_unlock()

    def can_be_restarted(self, ssh_server, client):
        """
        Check if the job can be restarted in the ssh server
        :param ssh_server: the ssh server
        :param client: the ssh client allowing the communication to the server
        :return: True if the job can be restarted, False otherwise
        """
        if os.path.exists(self.json_path):
            job = json.load(open(self.json_path, "r"))
            if 'job_id' not in job.keys():
                print(f"Job index not available.")
                ssh_server.locked = False
                return False
            values = ssh_server.execute(client, f"squeue | grep {job['job_id']}", return_stdout=True)
            if len(values["stdout"]) != 0:
                print(f"Job {job['job_id']} is still running.")
                ssh_server.locked = False
                return False
            values = ssh_server.execute(
                client,
                f"cat {ssh_server.repository_path}slurm-{job['job_id']}.out | grep 'Agent trained successfully!'",
                return_stdout=True
            )
            if len(values["stdout"]) != 0:
                print(f"Job {job['job_id']} finished successfully.")
                ssh_server.locked = False
                return False
        return True

    @staticmethod
    def create_on_local_computer(mutex, agent, env, project_name, params, forward_mutex=False):
        """
        Create a new job on the local computer
        :param mutex: the mutex to lock when accessing the file system
        :param agent: the job's agent
        :param env: the job's environment
        :param project_name: the name of the project running the job
        :param params: a dictionary containing the host and hardware on which the job is running
        :param forward_mutex: whether to forward the mutex to the Job constuctor
        :return: the created job
        """
        # Get json path
        json_path = Job.get_json_path(agent, env, project_name)

        # Check if job should be re-run
        if os.path.exists(json_path):
            job = json.load(open(json_path, "r"))
            if job["status"] != "crashed":
                print("Cannot re-run a task that have not crashed.")
                return None

        # Create a new job
        mutex.acquire()
        with open(json_path, mode="w+") as file:
            json.dump({
                "agent": agent,
                "env": env,
                "status": "pending",
                **params
            }, file, indent=2)
        mutex.release()

        return Job(mutex if forward_mutex else None, agent, env, project_name)

    def run(self, agent, env, projects_directory):
        """
        Run the next task in the queue
        """
        # Get agent and environment files
        agent_file = projects_directory + agent
        env_file = projects_directory + env

        # Run the training
        self.update("status", "running", save=False)
        self.update("start_time", datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
        try:
            # Redirect the standard output
            agent = agent.split("/")[-1].replace(".json", "")
            env = env.split("/")[-1].replace(".json", "").replace("_", "/")
            logging_dir = "/".join(projects_directory.split("/")[:-2])
            logging_dir += f"/logging/{env}/{agent}/"
            if not os.path.exists(logging_dir):
                os.makedirs(logging_dir)
            sys.stdout = open(logging_dir + f"stdout.txt", "w+")

            # Train the agent
            train_agent.train(agent_file, env_file)
            self.update("status", "success")
        except Exception as e:
            print(e)
            self.update("status", "crashed")

    @staticmethod
    def create_on_ssh_server(mutex, agent, env, project_name, params):
        """
        Create a new job on the ssh server
        :param mutex: the mutex to lock when accessing the file system
        :param agent: the job's agent
        :param env: the job's environment
        :param project_name: the name of the project running the job
        :param params: a dictionary containing the host and hardware on which the job is running
        :return: the created job
        """
        try:
            params["job_id"] = int(params["job_id"])
        except Exception as e:
            print(e)

        # Get json path
        json_path = Job.get_json_path(agent, env, project_name)

        # Create a new job
        mutex.acquire()
        with open(json_path, mode="w+") as file:
            json.dump({
                "agent": agent,
                "env": env,
                "status": "pending",
                **params
            }, file, indent=2)
        mutex.release()

        return Job(mutex, agent, env, project_name)

    @staticmethod
    def get_json_path(agent, env, project_name):
        """
        Getter
        :param agent: the agent json
        :param env: the environment json
        :param project_name: the project name
        :return: the hash corresponding to the (agent, environment) pair
        """
        conf = AnalysisConfig.instance
        hashed = agent + env
        hashed = hashlib.sha224(hashed.encode("utf-8")).hexdigest()
        return conf.projects_directory + f"{project_name}/jobs/{hashed}.json"
