import json
from datetime import datetime
import pytz


def nodebykey(nodes, key, value):
    return next((obj for obj in nodes
                 if key in obj and obj[key] == value), None)


def saveJSON(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as write_file:
        json.dump(data, write_file, ensure_ascii=False, indent=4)


def loadJSON(filepath):
    with open(filepath, 'r', encoding='utf-8') as read_file:
        return(json.load(read_file))


def stamp():
    return(int(datetime.timestamp(datetime.now(pytz.utc))))
