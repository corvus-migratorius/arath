#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from pathlib import Path

from ara.clients.offline import AraOfflineClient  # type: ignore


class Handler:
    def __init__(self):
        self.client = AraOfflineClient()
        self.playbooks = []
        self.actions: list[dict] = []
        self.report_template = """
{status}: "{taskname}"
{hostname} [{tagline}] "{playbook}"
{filename}:{lineno}
        """.strip()
        

    def run(self) -> None:
        self.fetch_playbooks()
        self.fetch_actions()
        self.report()


    def fetch_playbooks(self) -> None:
        self.playbooks = self.client.get("/api/v1/playbooks", status=["completed", "failed"], order="ended")


    def fetch_actions(self) -> None:
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
        modified = {
            "hostname": action["hostname_fact"] or action["hostname_inv"],
            "tagline":  " ".join(action["tags"]),
            **action
        }
        return self.report_template.format(**modified)

    def report(self) -> None:
        relevant = self.filter()
        for action in relevant:
            report = self.mk_template(action)
            print(report)

            #     task = self.client.get(f"/api/v1/tasks/{result['task']}")
            #     task["host"] = self.client.get(f"/api/v1/hosts/{result['host']}")
            #     task["status"] = result["status"]
                
            #     self.tasks.append(task)
                
            #     results["results"]:
            #     task = client.get("/api/v1/tasks/%s" % result["task"])
            #     host = client.get("/api/v1/hosts/%s" % result["host"])

            #     if(result["status"] not in ["ok", "skipped"]):
            #         if_something_changed = True

            #         print(template.format(
            #         timestamp=result["ended"],
            #         status=result["status"],
            #         host=host["name"],
            #         task=task["name"],
            #         task_file=task["path"],
            #         lineno=task["lineno"]
            #         ))

            #         tg_message = tg_message + template.format(
            #         timestamp=result["ended"],
            #         status=result["status"],
            #         host=host["name"],
            #         task=task["name"],
            #         task_file=task["path"],
            #         lineno=task["lineno"]
            #         ) + "\n" + "\n"
            # print("\n")


def main():
    handler = Handler()

    handler.run()

    # handler.fetch_playbooks()
    # handler.fetch_actions()

    # for action in handler.actions:
    #     print(action)

    # client = AraOfflineClient()

    # playbooks = client.get("/api/v1/playbooks", status=["completed", "failed"], order="ended")

    # print(f"discovered playbook runs: {len(playbooks['results'])}")

    # for playbook in playbooks["results"]:
    #     print("playbook: " + playbook["path"])

    #     if(playbook["status"] == "completed"):
    #         print("playbook completed at: " + playbook["ended"])
    #     else:
    #         print("playbook failed at: " + playbook["ended"])


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
