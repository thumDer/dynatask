import datetime
import requests

import helper

import logging
import json
import configparser
from defaultconfig import configPath
import googlecal

config = configparser.ConfigParser()
config.read(configPath)

fileURL = config['dynalist']['file_url']
docURL = config['dynalist']['doc_url']
key = config['dynalist']['api_key']
tasklistTag = config['dynalist']['tasklist_tag']
taskTag = config['dynalist']['task_tag']
alarmTag = config['dynalist']['alarm_prefix']


def FetchData():

    data = {'files': []}

    if key != '':
        r = requests.post(fileURL, json={"token": key})
    else:
        logging.error('Dynalist API key is empty in config.')

    fileData = r.json()
    files = fileData['files']

    for i in files:
        if i['type'] == 'document':
            fileId = i['id']
            r = requests.post(docURL, json={"token": key, "file_id": fileId})
            docData = r.json()
            nodes = docData['nodes']
            fObj = {
                'name': i['title'],
                'id': fileId,
                'nodes': nodes
            }

            data['files'].append(fObj)

    with open('./data/dynalist.json', 'w', encoding='utf-8') as write_file:
        json.dump(data, write_file, ensure_ascii=False, indent=4)

    flatData = []
    for i in data['files']:
        fileName = i['name']
        fileId = i['id']
        for j in i['nodes']:
            j['filename'] = fileName
            j['fileid'] = fileId
            flatData.append(j)

    for node in flatData:
        if 'children' in node:
            childrenIds = node['children']
            for childId in childrenIds:
                childNode = nodebyid(flatData, childId)
                childNode['parentid'] = node['id']

    with open('./data/dynalist_flattened.json',
              'w', encoding='utf-8') as write_file:
        json.dump(flatData, write_file, ensure_ascii=False, indent=4)

    return(flatData)


def FilterData(nodes):

    filteredData = []
    for node in nodes:
        try:
            parentNode = nodebyid(nodes, node['parentid'])
        except Exception:
            continue
        isTask = False
        if '!(' in node['content'] or '!(' in node['note']:
            isTask = True
        if taskTag in node['content']:
            isTask = True
        if tasklistTag in parentNode['content']:
            isTask = True

        url = "https://dynalist.io/d/{}#z={}".format(node['fileid'],
                                                     node['id'])

        path = ''
        loopNode = node
        while True:
            parentId = loopNode['parentid']
            if parentId == 'root':
                break
            parentNode = nodebyid(nodes, parentId)
            parentName = parentNode['content']
            loopNode = parentNode
            path = parentName + ' > ' + path

        children = ''
        if 'children' in node:
            for childId in node['children']:
                child = nodebyid(nodes, childId)
                if 'checked' in child and child['checked']:
                    children += '[X] ' + child['content']
                else:
                    children += '[ ] ' + child['content']

        dynalist_info = (
            'URL:/n{} /n/nFile:/n{}/n/n'
            'Path:/n{}/n/nChildren:/n{}'
            .format(url, node['filename'], path, children))

        node['dynalist_info'] = dynalist_info

        if isTask:
            filteredData.append(node)

    with open('./data/dynalist_filtered.json',
              'w', encoding='utf-8') as write_file:
        json.dump(filteredData, write_file, ensure_ascii=False, indent=4)

    return(filteredData)


def ConvertData(nodes):
    convertedData = []
    for node in nodes:
        obj = {}
        if '!(' in node['content']:
            due = node['content'].split('!(', 1)[1].split(')', 1)[0]
            name = node['content'].replace(
                ' !(' + due + ')', '').replace(' ' + taskTag, '').rstrip()

            if len(due) == 10:
                date = due
                time = ''
                # allday = True
            else:
                date = due[:10]
                time = due[10:]
                # allday = False

            note = node['note']

            obj['name'] = name
            obj['note'] = note
            obj['date'] = date
            obj['time'] = time

            if alarmTag in name:
                alarm = name.split(alarmTag, 1)[1].split(' ')[0]
                obj['alarm'] = alarm
            else:
                obj['alarm'] = ''

            if 'checked' in node and node['checked']:
                obj['checked'] = True
            else:
                obj['checked'] = False

            dynalist_id = node['id']
            dynalist_file_id = node['fileid']
            # caldav_id = dynalist_id

            obj['dynalist_id'] = dynalist_id
            obj['parentid'] = node['parentid']
            obj['dynalist_file_id'] = dynalist_file_id
            obj['dynalist_info'] = node['dynalist_info']

            convertedData.append(obj)

        with open('./data/dynalist_converted.json',
                  'w', encoding='utf-8') as write_file:
            json.dump(convertedData, write_file, ensure_ascii=False, indent=4)

    return(convertedData)


def run():

    if key != '':
        r = requests.post(fileURL, json={"token": key})
    else:
        logging.error('Dynalist API key is empty in config.')

    data = r.json()

    files = data['files']

    fileNames = [i['title'] for i in files]

    logging.info("Found the following documents:")
    logging.info(fileNames)

    calObjs = []

    for i in files:
        if i['type'] == "folder":
            pass
        else:
            fileName = i['title']
            fileId = i['id']

            r = requests.post(docURL, json={"token": key, "file_id": fileId})

            docData = r.json()
            try:
                nodes = docData['nodes']

                for node in nodes:

                    event = process_content(nodes, node, fileName, fileId)

                    if event != "":
                        calObjs.append(event)

            except Exception as e:
                # logging.warning(i)
                # logging.warning(docData)
                logging.warning(e)

    logging.info("Found {} events.".format(len(calObjs)))

    googlecal.pushtogoogle(calObjs)


def process_content(nodes, node, fileName, fileId):
    content = node['content']
    id = node['id']
    try:
        checked = node['checked']
    except Exception:
        checked = False

    if checked is not True and "!(" in content:
        content1, content2 = content.split("!(", 1)
        content21, content22 = content2.split(")", 1)

        date = content21

        if content22 != "":
            name = "{} {}".format(
                content1.rstrip(), content22.lstrip())
        else:
            name = content1

        if len(date) == 10:
            date_obj = datetime.datetime.strptime(
                date, '%Y-%m-%d')
            allday = True
        else:
            date_obj = datetime.datetime.strptime(
                date, '%Y-%m-%d %H:%M')
            allday = False

        url = "https://dynalist.io/d/{}#z={}".format(fileId, id)

        ancestors = "Source: {}\n\n".format(fileName)

        children = ""
        try:
            childrenNodes = node['children']
            logging.debug(childrenNodes)
            if childrenNodes:
                for childId in childrenNodes:
                    children += "- " + contentbyid(nodes, childId) + "\n"
                children += "\n"
        except Exception:
            logging.debug("No children.")
        note = ""

        description = note + ancestors + children + url

        if "#alarm" in name:
            alarm = name.split("#alarm")[1]
            if " " in alarm:
                alarm = alarm.split(" ")[0]
        else:
            alarm = ""

        logging.debug("Name: {}, Date: {}, Alarm: {}".format(
            name, date_obj, alarm))

        co = helper.CalObj(name, date_obj, allday, description, alarm)

        return co
    else:
        return ""


def contentbyid(json_object, id):
    return [obj for obj in json_object if obj['id'] == id][0]['content']


def nodebyid(nodes, id):
    return next(obj for obj in nodes if obj['id'] == id)


ConvertData(FilterData(FetchData()))
