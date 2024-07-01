#!/usr/bin/env python3
# Import the client
from ara.clients.http import AraHttpClient

# Import some libs
from datetime import datetime, timedelta
import requests

# Import config parser and parse
import configparser

config = configparser.ConfigParser()
config.read(r'config.txt')
# It contains vars "tg_TOKEN", "tg_chat_id", "endpoint"

tg_TOKEN = config.get('tg', 'tg_TOKEN')
tg_chat_id = config.get('tg', 'tg_chat_id')
endpoint = config.get('ara', 'endpoint')

# Just set default value
tg_message = "none"

# Instanciate the HTTP client with an endpoint where an API server is listening
client = AraHttpClient(endpoint=endpoint)

f = open("ISOTIME", "r")
last_time_parsed = f.readline()
f.close()

time_to_parse= last_time_parsed

last_time_parsed = datetime.now()
last_time_parsed = last_time_parsed.isoformat()

# Get a list of failed playbooks
# /api/v1/playbooks
# Example ended_after for test api is "2021-09-09T22:12:51.607864Z". Write it to a "ISOTIME" file.
playbooks = client.get("/api/v1/playbooks", status=["completed", "failed"], order="ended", ended_after=time_to_parse)

f = open("ISOTIME", "w")
f.write(last_time_parsed)
f.close()

# If there are any results from our query, get more information about the
# failure and print something helpful
template = "{timestamp}: {host} {status} '{task}' ({task_file}:{lineno})"

for playbook in playbooks["results"]:
    tg_message = "```\n"

    print("playbook: " + playbook["path"])
    tg_message = tg_message + "playbook: " + playbook["path"] + "\n"

    if(playbook["status"] == "completed"):
        print("playbook completed at: " + playbook["ended"])
        tg_message = tg_message + "playbook completed at: " + playbook["ended"] + "\n"
    else:
        print("playbook failed at: " + playbook["ended"])
        tg_message = tg_message + "playbook failed at: " + playbook["ended"] + "\n"

    tg_message = tg_message + "\n"

    results = client.get("/api/v1/results?playbook=%s" % playbook["id"])

    if_something_changed = False

    # For each result, print the task and host information
    for result in results["results"]:
        task = client.get("/api/v1/tasks/%s" % result["task"])
        host = client.get("/api/v1/hosts/%s" % result["host"])

        if(result["status"] not in ["ok", "skipped"]):
            if_something_changed = True

            print(template.format(
               timestamp=result["ended"],
               status=result["status"],
               host=host["name"],
               task=task["name"],
               task_file=task["path"],
               lineno=task["lineno"]
            ))

            tg_message = tg_message + template.format(
               timestamp=result["ended"],
               status=result["status"],
               host=host["name"],
               task=task["name"],
               task_file=task["path"],
               lineno=task["lineno"]
            ) + "\n" + "\n"
    print("\n")

    # Do not send message if noting changed
    if(not(if_something_changed)):
        continue

    tg_message = tg_message + "\n" + "```"
    tg_url = f"https://api.telegram.org/bot{tg_TOKEN}/sendMessage?chat_id={tg_chat_id}&text={tg_message}&parse_mode=MarkdownV2"
    requests.get(tg_url).json() # Send message to tg
