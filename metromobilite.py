#!/usr/bin/env python3

from os.path import expanduser
from datetime import datetime, timedelta
from urllib.parse import quote
import json, yaml
import requests

CONFIG=expanduser('~/.config/argos-widgets/metromobilite.yaml')

with open(CONFIG, 'r') as configfile:
    config = yaml.load(configfile, Loader=yaml.BaseLoader)

if "metromobilite" in config:
    config = config["metromobilite"]

def getStopInfo(stopquery):
    url = "http://data.metromobilite.fr/api/findType/json?types=arret&query={}".format(stopquery)
    return requests.get(url).json()["features"][0]

def getLineInfo(lineid):
    url = "https://data.metromobilite.fr/api/routers/default/index/routes?codes={}".format(lineid)
    return requests.get(url).json()[0]

def getSchedule(stopid):
    url = "https://data.metromobilite.fr/api/routers/default/index/clusters/{}/stoptimes".format(stopid)
    raw = requests.get(url).json()
    result={}
    for item in raw:
        lineid = ":".join(item["pattern"]["id"].split(':')[:2])
        dest = item["pattern"]["desc"]
        if lineid not in result:
            result[lineid] = []
        for trip in item["times"]:
            result[lineid].append(
                    {
                        "time": trip["realtimeArrival"],
                        "rt": trip["realtime"],
                        "dest": dest
                    }
            )
    for item in result:
        result[item]=sorted(result[item], key = lambda i: i["time"])
    return result

if __name__== "__main__":
    print("Bus | iconName=mark-location-symbolic")
    print("---")
    for stopquery in config["stations"]:
        stop = getStopInfo(quote(stopquery))
        stopid = stop["properties"]["id"]
        stopname = stop["properties"]["LIBELLE"]
        schedule = getSchedule(stopid)
        now = datetime.now()
        todayref = now.replace(hour=0, minute=0, second=0, microsecond=0)
        for line in schedule:
            lineinfo = getLineInfo(line)
            print("{} : <span foreground=\"#{}\" background=\"#{}\">{}</span>".format(
                stopname,
                lineinfo["textColor"],
                lineinfo["color"],
                lineinfo["shortName"]
            ))
            for trip in schedule[line]:
                abstime = todayref + timedelta(0,trip["time"])
                reltime = abstime - now
                if trip["rt"]:
                    icon = "application-rss+xml-symbolic"
                else:
                    icon = "document-open-recent-symbolic"
                remainingsec = reltime.seconds
                if remainingsec // 3600 == 0:
                    remaining = "{}m".format(remainingsec // 60)
                else:
                    remaining = "{}h {}m".format(remainingsec // 3600, remainingsec % 3600 // 60)
                print("--{} <i>({})</i> → <b>{}</b> | iconName={}".format(
                    abstime.strftime('%H:%M'),
                    remaining,
                    trip["dest"],
                    icon
                    ))
