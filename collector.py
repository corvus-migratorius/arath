"""
Implements a class for collecting relevant task information from ARA.
"""

from datetime import datetime as dt
from pathlib import Path

from ara.clients.offline import AraOfflineClient  # type: ignore


class Collector:
    """
    The ARATH Collector class.
    """
    def __init__(self):
        self.client = AraOfflineClient()
        self.playbooks = []
        self.actions: list[dict] = []

        self.filtered = []
        
        self.timestamp_path = ".arath.timestamp"
        self.timestamp_now = dt.now().isoformat()
        self.timestamp_prev = self.load_timestamp()

        self.report_template = """
{status}: "{taskname}"
{hostname} [{tagline}] "{playbook}"
{filename}:{lineno}
        """.strip()


    def run(self) -> None:
        """
        Perform the fetch -> filter -> report cycle.
        """
        self.fetch_playbooks()
        self.fetch_actions()
        
        self.filtered = self.filter()

        self.report(self.filtered)

        # only if the run was successful
        self.update_timestamp()


    def update_timestamp(self):
        """
        Save to disk the timestamp of the beginning of this run.
        """
        with open(self.timestamp_path, "w", encoding="utf-8") as file:
            file.write(self.timestamp_now)


    def load_timestamp(self) -> dt:
        """
        If timestamp file exists, return its contents, else epoch start.
        """
        try:
            with open(self.timestamp_path, "r", encoding="utf-8") as file:
                timestamp_prev = file.read()
            return dt.fromisoformat(timestamp_prev)
        except FileNotFoundError as error:
            print(error)
            return dt.fromisoformat("1970-01-01T00:00:00.0Z")


    def fetch_playbooks(self) -> None:
        """
        Fetch from ARA API playbook objects generated after the previous run started.
        """
        self.playbooks = self.client.get(
            "/api/v1/playbooks",
            status=["completed", "failed"],
            order="ended",
            ended_after=self.timestamp_prev
        )


    def fetch_actions(self) -> None:
        """
        Fetch from ARA API task objects for the relevant plays.
        """
        print(f"current timestamp: {self.timestamp_now}")
        print(f"previous timestamp: {self.timestamp_prev}")

        # For each result, print the task and host information
        for playbook in self.playbooks["results"]:
            results = self.client.get(f"/api/v1/results?playbook={playbook['id']}")["results"]
            
            for result in results:
                task = self.client.get(f"/api/v1/tasks/{result['task']}")
                host = self.client.get(f"/api/v1/hosts/{result['host']}")
                hostname_inv = host["name"]
                hostname_fact = host["facts"]["ansible_hostname"] 
                filename = Path(task["file"]["path"]).name
                playbook_name = task["play"]["name"]
                tags = task["tags"] 
                
                self.actions.append({
                    "hostname_fact": hostname_fact,
                    "hostname_inv": hostname_inv,
                    "playbook": playbook_name,
                    "tags": tags,
                    "taskname": task["name"],
                    "status": result["status"],
                    "filename": filename,
                    "lineno": task["lineno"],
                    "ended": result["ended"]
                })


    def filter(self, statuses: list[str] = ["ok", "skipped"]) -> list[dict]:
        """
        Filter out irrelevant statuses.
        """
        return [action for action in self.actions if action["status"] not in statuses]


    def mk_template(self, action: dict) -> str:
        """
        Fill the report template string for the given "action" (task).
        """
        modified = {
            "hostname": action["hostname_fact"] or action["hostname_inv"],
            "tagline":  " ".join(action["tags"]),
            **action
        }
        return self.report_template.format(**modified)


    def report(self, relevant: list) -> None:
        """
        Report the tasks matching the filter criteria.
        """
        for action in relevant:
            report = self.mk_template(action)
            print(report)
