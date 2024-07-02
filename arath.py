#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from datetime import datetime as dt
from pathlib import Path

from ara.clients.offline import AraOfflineClient  # type: ignore


class Handler:
    """
    The ARATH handler class.
    """
    def __init__(self):
        self.client = AraOfflineClient()
        self.playbooks = []
        self.actions: list[dict] = []
        
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
        self.report()

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


    def report(self) -> None:
        """
        Report the tasks matching the filter criteria.
        """
        relevant = self.filter()
        for action in relevant:
            report = self.mk_template(action)
            print(report)


def main():
    handler = Handler()

    handler.run()


if __name__ == "__main__":
    main()


# import requests
# from ara.clients.http import AraHttpClient

# # Import some libs
# from datetime import datetime, timedelta

# # Import config parser and parse
# import configparser

# config = configparser.ConfigParser()
# config.read(r'config.txt')
# # It contains vars "tg_TOKEN", "tg_chat_id", "endpoint"

# tg_TOKEN = config.get('tg', 'tg_TOKEN')
# tg_chat_id = config.get('tg', 'tg_chat_id')
# endpoint = config.get('ara', 'endpoint')

# # Just set default value
# tg_message = "none"

# # Instanciate the HTTP client with an endpoint where an API server is listening
# client = AraHttpClient(endpoint=endpoint)

# f = open("ISOTIME", "r")
# last_time_parsed = f.readline()
# f.close()

# time_to_parse= last_time_parsed

# last_time_parsed = datetime.now()
# last_time_parsed = last_time_parsed.isoformat()

# # Get a list of failed playbooks
# # /api/v1/playbooks
# # Example ended_after for test api is "2021-09-09T22:12:51.607864Z". Write it to a "ISOTIME" file.
# playbooks = client.get("/api/v1/playbooks", status=["completed", "failed"], order="ended", ended_after=time_to_parse)

# f = open("ISOTIME", "w")
# f.write(last_time_parsed)
# f.close()

# # If there are any results from our query, get more information about the
# # failure and print something helpful
# template = "{timestamp}: {host} {status} '{task}' ({task_file}:{lineno})"

# for playbook in playbooks["results"]:
#     tg_message = "```\n"

#     print("playbook: " + playbook["path"])
#     tg_message = tg_message + "playbook: " + playbook["path"] + "\n"

#     if(playbook["status"] == "completed"):
#         print("playbook completed at: " + playbook["ended"])
#         tg_message = tg_message + "playbook completed at: " + playbook["ended"] + "\n"
#     else:
#         print("playbook failed at: " + playbook["ended"])
#         tg_message = tg_message + "playbook failed at: " + playbook["ended"] + "\n"

#     tg_message = tg_message + "\n"

#     results = client.get("/api/v1/results?playbook=%s" % playbook["id"])

#     if_something_changed = False

#     # For each result, print the task and host information
#     for result in results["results"]:
#         task = client.get("/api/v1/tasks/%s" % result["task"])
#         host = client.get("/api/v1/hosts/%s" % result["host"])

#         if(result["status"] not in ["ok", "skipped"]):
#             if_something_changed = True

#             print(template.format(
#                timestamp=result["ended"],
#                status=result["status"],
#                host=host["name"],
#                task=task["name"],
#                task_file=task["path"],
#                lineno=task["lineno"]
#             ))

#             tg_message = tg_message + template.format(
#                timestamp=result["ended"],
#                status=result["status"],
#                host=host["name"],
#                task=task["name"],
#                task_file=task["path"],
#                lineno=task["lineno"]
#             ) + "\n" + "\n"
#     print("\n")

#     # Do not send message if noting changed
#     if(not(if_something_changed)):
#         continue

#     tg_message = tg_message + "\n" + "```"
#     tg_url = f"https://api.telegram.org/bot{tg_TOKEN}/sendMessage?chat_id={tg_chat_id}&text={tg_message}&parse_mode=MarkdownV2"
#     requests.get(tg_url).json() # Send message to tg
