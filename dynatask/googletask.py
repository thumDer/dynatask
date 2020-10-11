import datetime
import requests

import logging
import configparser
from modules.defaultconfig import configPath #pylint: disable=E0401
import googlecal #pylint: disable=E0401

config = configparser.ConfigParser()
config.read(configPath)

fileURL = config['dynalist']['file_url']
docURL = config['dynalist']['doc_url']
key = config['dynalist']['api_key']


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


def contentbyid(json_object, id):
    return [obj for obj in json_object if obj['id'] == id][0]['content']
