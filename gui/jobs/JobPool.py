import queue
from datetime import datetime
from multiprocessing import Process
from threading import Thread


class JobPool:
    """
    A job pool that allows easy interruption of jobs
    """

    def __init__(self):
        """
        Constructor
        """
        self.current_process = None
        self.current_job = None
        self.jobs = queue.Queue()

    def submit(self, job, **kwargs):
        """
        Submit a task to the pool
        :param job: the corresponding job
        :param kwargs: the job's arguments
        """
        self.jobs.put((job, kwargs))
        if self.current_process is None:
            self.run_next_task()

    def run_next_task(self):
        """
        Run the next job in the queue
        """
        if self.jobs.empty():
            return
        job, kwargs = self.jobs.get()
        self.current_process = Process(target=job.display_efe_prediction, args=kwargs.values())
        self.current_process.start()
        job.update("status", "running", save=False)
        job.update("start_time", datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
        self.current_job = job
        Thread(target=self.call_callback, args=(self.current_process, )).start()

    def call_callback(self, process, callback=None):
        """
        Call the callback function action after the process ends
        :param process: the process
        :param callback: the callback
        """
        process.join()
        if callback is None:
            self.run_next_task()
        else:
            callback()

    def stop_job(self, job_json):
        """
        Stop a specific job
        :param job_json: the json describing the job to stop
        """
        if self.current_job is not None \
                and self.current_job.json["agent"] == job_json["agent"] \
                and self.current_job.json["env"] == job_json["env"]:
            self.stop(all_jobs=False)
        else:
            jobs = list(self.jobs.queue)
            for i, (job, _) in enumerate(jobs):
                if job.json["agent"] == job_json["agent"] and job.json["env"] == job_json["env"]:
                    del jobs[i]
                    break
            self.jobs = queue.Queue()
            for job in jobs:
                self.jobs.put(job)

    def stop(self, all_jobs=True):
        """
        Stop the current process
        :param all_jobs: whether to add all jobs
        """
        # Stop current process
        if self.current_process is not None:
            is_alive = self.current_process.is_alive()
            self.current_process.terminate()
            self.current_process = None
            if is_alive:
                self.current_job.update("status", "crashed")
            self.current_job = None

        # Kill all jobs in the pool or start a new process
        if all_jobs:
            while not self.jobs.empty():
                job, _ = self.jobs.get()
                job.update("status", "crashed")
        else:
            self.run_next_task()


