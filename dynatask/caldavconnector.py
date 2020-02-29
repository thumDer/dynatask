from datetime import date, datetime, timedelta, timezone
import caldav
from caldav.elements import dav, cdav
from icalendar import Calendar, Event, Todo, Alarm
import configparser
import pytz
import json
from helper import saveJSON, loadJSON, nodebykey
from cache import timestamp

config = configparser.ConfigParser()

config.read('./dynatask/config.ini')

url = config['caldav']['task_url']
user = config['caldav']['user']
password = config['caldav']['password']

server_url = url.split('.php')[0]+('.php')

# with open('./data/dynalist_converted.json',
#           'r', encoding='utf-8') as read_file:
#     data = json.load(read_file)


def TodoFromJSON(cal, data):
    tz = pytz.timezone("Europe/Budapest")
    try:
        description = data['note']+data['dynalist_info']
    except Exception:
        description = ''
    duedate = data['date'].replace('-', '')
    time = data['time'].replace(':', '')
    if not duedate == '':
        Y = int(duedate[:4])
        m = int(duedate[4:6])
        D = int(duedate[6:8])
        if not time == '':
            H = int(time[:2])
            M = int(time[2:4])

    if cal is None:
        cal = Calendar()
        cal.add('prodid', '-//Dynatask//')
        cal.add('version', '2.0')
        todo = Todo()
        if 'dynalist_id' in data:
            todo.add('uid', data['dynalist_id']+'@dynatask')
            todo.add('X-DYNATASK-DYNALISTID', data['dynalist_id'])
        elif 'caldav_uid' in data:
            todo.add('uid', data['caldav_uid'])
        todo.add('summary', data['name'])
        created = datetime.now(pytz.utc)
        todo.add('dtstamp', created)
        todo.add('created', created)
        todo.add('last-modified', created)
        if not duedate == '':
            if not time == '':
                todo.add('due', datetime(Y, m, D, H, M,
                         tzinfo=tz))
            else:
                todo.add('due', datetime(Y, m, D).date())
        todo.add('description', description)

        if 'checked' in data:
            if data['checked']:
                todo.add('status', 'COMPLETED')
            else:
                todo.add('status', 'NEEDS-ACTION')

        if 'alarm' in data and not data['alarm'] == '':
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('trigger', timedelta(minutes=-int(data['alarm'])))
            todo.add_component(alarm)

        cal.add_component(todo)
        return(cal)
    # else:
    #     for todo in cal.walk('vtodo'):
    #         todo


def JSONFromTodo(data):
    array = []
    for todo in data:
        obj = {}
        obj['name'] = todo['summary']
        if 'description' in todo:
            obj['note'] = todo['description'].split('----')[0]
        else:
            obj['note'] = ''
        obj['caldav_uid'] = todo['uid']
        if 'X-DYNATASK-DYNALISTID' in todo:
            obj['dynalist_id'] = todo['X-DYNATASK-DYNALISTID']
        if 'status' in todo:
            if todo['status'] == 'COMPLETED':
                obj['checked'] = True
            else:
                obj['checked'] = False
        if 'due' in todo:
            obj['date'] = todo['due'].dt.strftime('%Y-%m-%d')
            if isinstance(todo['due'].dt, datetime):
                obj['time'] = todo['due'].dt.strftime('%H:%M')
            else:
                obj['time'] = ''
        else:
            obj['date'] = ''
            obj['time'] = ''
        if 'dtstamp' in todo:
            obj['caldav_dtstamp'] = int(todo['dtstamp'].dt.
                                        replace(tzinfo=timezone.utc).
                                        timestamp()*1000)
        if 'created' in todo:
            obj['caldav_created'] = int(todo['created'].dt.
                                        replace(tzinfo=timezone.utc).
                                        timestamp()*1000)
        if 'last-modified' in todo:
            obj['caldav_modified'] = int(todo['last-modified'].dt.
                                         replace(tzinfo=timezone.utc).
                                         timestamp()*1000)
        array.append(obj)
    return(array)


def getcalendars():
    client = caldav.DAVClient(server_url, username=user, password=password)
    principal = client.principal()
    calendars = principal.calendars()
    return(calendars)


def pull():
    todos = []
    calendars = getcalendars()

    for cal in calendars:
        if cal.canonical_url == url:
            for caldavtodo in cal.todos(include_completed=True):
                cal = Calendar.from_ical(caldavtodo.data)
                for todo in cal.walk('vtodo'):
                    todos.append(todo)
    data = JSONFromTodo(todos)
    saveJSON('./data/pulltodos.json', data)
    return(data)


def push(data):
    lastsync = timestamp()
    calendars = getcalendars()

    for caldavcal in calendars:
        if caldavcal.canonical_url == url:
            for caldavtodo in caldavcal.todos(include_completed=True):
                cal = Calendar.from_ical(caldavtodo.data)
                for component in cal.walk('vtodo'):
                    uid = component['uid']
                try:
                    obj = nodebykey(data, 'caldav_uid', uid)
                except Exception:
                    obj = None
                if obj is None:
                    print('Deleting: {}'.format(caldavtodo))
                    caldavtodo.delete()

            for i in data:
                # print('{} > {}'.format(i['cache_modified'], lastsync))
                if i['cache_modified'] > lastsync:
                    todoIcal = TodoFromJSON(None, i).to_ical()
                    todo = caldavcal.add_todo(todoIcal)
                    print('{} created / updated!'.format(todo))


if __name__ == '__main__':
    pull()
