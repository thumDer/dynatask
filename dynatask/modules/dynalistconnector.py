import requests
import logging
import configparser
from .defaultconfig import configPath
from .helper import nodebykey, saveJSON

config = configparser.ConfigParser()
config.read(configPath)

fileURL = config['dynalist']['file_url']
docURL = config['dynalist']['doc_url']
key = config['dynalist']['api_key']
tasklistTag = config['dynalist']['tasklist_tag']
taskTag = config['dynalist']['task_tag']
excludeTag = config['dynalist']['exclude_tag']
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

    saveJSON('./data/dynalist_data_raw.json', data)

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
                childNode = nodebykey(flatData, 'id', childId)
                childNode['parentid'] = node['id']

    saveJSON('./data/dynalist_data_flattened.json', flatData)

    return(flatData)


def FilterData(nodes):

    filteredData = []
    for node in nodes:
        try:
            parentNode = nodebykey(nodes, 'id', node['parentid'])
        except Exception:
            continue
        isTask = False
        if '!(' in node['content'] or '!(' in node['note']:
            isTask = True
        if taskTag in node['content']:
            isTask = True
        if tasklistTag in parentNode['content']:
            isTask = True
        if excludeTag in node['content']:
            isTask = False

        path = ''
        loopNode = node
        while True:
            parentId = loopNode['parentid']
            if parentId == 'root':
                break
            parentNode = nodebykey(nodes, 'id', parentId)
            parentName = parentNode['content']
            loopNode = parentNode
            path = parentName + ' > ' + path
        path = node['filename'] + ' > ' + path

        node['path'] = path

        children = ''
        if 'children' in node:
            for childId in node['children']:
                child = nodebykey(nodes, 'id', childId)
                if 'checked' in child and child['checked']:
                    children += '[X] ' + child['content'] + '\n'
                else:
                    children += '[ ] ' + child['content'] + '\n'

        node['children'] = children

        if isTask:
            filteredData.append(node)

    saveJSON('./data/dynalist_data_filtered.json', filteredData)

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
                time = due[11:]
                # allday = False

        elif taskTag in node['content']:
            name = node['content'].replace(' '+taskTag, '').rstrip()
            date = ''
            time = ''
        else:
            name = node['content']
            date = ''
            time = ''

        note = node['note']

        url = 'https://dynalist.io/d/{}#z={}'.format(node['fileid'],
                                                     node['id'])

        obj['name'] = name
        obj['note'] = note
        obj['url'] = url
        obj['date'] = date
        obj['time'] = time

        if not alarmTag == '' and alarmTag in name:
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

        dynalist_info = (
            '----\n'
            '{}\n{}\n\n{}'
            .format(node['path'], url, node['children']))

        obj['dynalist_id'] = dynalist_id
        obj['dynalist_parent_id'] = node['parentid']
        obj['dynalist_file_id'] = dynalist_file_id
        obj['dynalist_info'] = dynalist_info
        obj['dynalist_created'] = int(node['created']/1000)
        obj['dynalist_modified'] = int(node['modified']/1000)

        convertedData.append(obj)

        saveJSON('./data/dynalist_data_converted.json', convertedData)

    return(convertedData)


def pull():
    data = ConvertData(FilterData(FetchData()))
    logging.info('Items pulled from dynalist: {}'.format(len(data)))
    for i in data:
        logging.debug('Dynalist item: {}'.format(i['name']))
    return(data)


if __name__ == '__main__':
    pull()