import datetime
import requests
import helper
import config
import logging
import googlecal

fileURL = config.file_url
docURL = config.doc_url
key = config.dynalist_apikey


def run():

    r = requests.post(fileURL, json={"token": key})

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
