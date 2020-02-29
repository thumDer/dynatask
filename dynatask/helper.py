import json
from datetime import datetime
import pytz


class CalObj:
    def __init__(self, name, date, allday, description, alarm):
        self.name = name
        self.date = date
        self.allday = allday
        self.description = description
        self.alarm = alarm


def nodebyid(nodes, id):
    return next(obj for obj in nodes if obj['id'] == id)


def nodebykey(nodes, key, value):
    return next((obj for obj in nodes if obj[key] == value), None)


def saveJSON(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as write_file:
        json.dump(data, write_file, ensure_ascii=False, indent=4)


def loadJSON(filepath):
    with open(filepath, 'r', encoding='utf-8') as read_file:
        return(json.load(read_file))


def complementdata(targetnode, sourcenode):
    for i in sourcenode:
        if i not in targetnode:
            targetnode[i] = sourcenode[i]


def stamp():
    return(int(datetime.timestamp(datetime.now(pytz.utc))*1000))
