from datetime import datetime, timedelta, timezone
import caldav
from icalendar import Calendar, Todo, Alarm
import configparser
import pytz
from .helper import saveJSON, nodebykey
import logging

config = configparser.ConfigParser()

config.read('./dynatask/config.ini')

url = config['caldav']['task_url']
user = config['caldav']['user']
password = config['caldav']['password']


def TodoFromJSON(cal, data):
    tz = pytz.timezone("Europe/Budapest")
    if 'dynalist_info' in data:
        if data['note'] == '':
            description = data['dynalist_info']
        else:
            description = data['note'] + '\n' + data['dynalist_info']
    else:
        description = data['note']
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
            todo.add('uid', data['caldav_uid'])
            todo.add('X-DYNATASK-DYNALISTID', data['dynalist_id'])
        elif 'caldav_uid' in data:
            todo.add('uid', data['caldav_uid'])
        todo.add('summary', data['name'])
        now = datetime.now(pytz.utc)
        todo.add('dtstamp', now)
        todo.add('created', now)
        todo.add('last-modified', now)
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
                todo.add('completed', datetime.now(pytz.utc))
                todo.add('percent-complete', '100')
            else:
                todo.add('status', 'NEEDS-ACTION')
                todo.add('percent-complete', '0')

        if 'caldav_parent' in data:
            todo.add('related-to', data['caldav_parent'])

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
            if '\n----' in todo['description']:
                note = todo['description'].split('\n----')[0]
            elif todo['description'].startswith('----'):
                note = ''
            else:
                note = todo['description']
            obj['note'] = note
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
                                        timestamp())
        if 'created' in todo:
            obj['caldav_created'] = int(todo['created'].dt.
                                        replace(tzinfo=timezone.utc).
                                        timestamp())
        if 'last-modified' in todo:
            obj['caldav_modified'] = int(todo['last-modified'].dt.
                                         replace(tzinfo=timezone.utc).
                                         timestamp())
        array.append(obj)
    return(array)


def getcalendars():
    client = caldav.DAVClient(url, username=user, password=password)
    # principal = client.principal()
    # calendars = principal.calendars()
    calendar = caldav.objects.Calendar(client=client, url=url)
    # return(calendars)
    return(calendar)


calendar = getcalendars()


def pull():
    todos = []

    for caldavTodo in calendar.todos(include_completed=True):
        icalTodo = Calendar.from_ical(caldavTodo.data)
        for todo in icalTodo.walk('vtodo'):
            todos.append(todo)

    # for cal in calendars:
    #     if cal.canonical_url == url:
    #         for caldavtodo in cal.todos(include_completed=True):
    #             cal = Calendar.from_ical(caldavtodo.data)
    #             for todo in cal.walk('vtodo'):
    #                 todos.append(todo)
    data = JSONFromTodo(todos)
    saveJSON('./data/caldav_data.json', data)
    logging.info('Pulled {} items from CalDAV...'.format(len(data)))
    for i in data:
        logging.debug('Caldav item: {}'.format(i['name']))
    return(data)


def push(cache):
    logging.info('Updating CalDAV...')
    data = cache['data']
    delItems = 0
    newItems = 0
    lastsync = cache['synced']

    for caldavTodo in calendar.todos(include_completed=True):
        icalTodo = Calendar.from_ical(caldavTodo.data)
        for todo in icalTodo.walk('vtodo'):
            uid = todo['uid']
        try:
            obj = nodebykey(data, 'caldav_uid', uid)
        except Exception:
            obj = None
        if obj is None:
            logging.debug('Deleting "{}"...'.format(caldavTodo))
            caldavTodo.delete()
            delItems += 1
        elif obj['cache_modified'] > lastsync:
            todo = TodoFromJSON(None, obj)
            caldavTodo.data = todo.to_ical()

    logging.info('Deleted {} items on CalDAV'.format(delItems))

    for i in data:
        if i['cache_modified'] > lastsync:
            todo = TodoFromJSON(None, i)
            todoIcal = todo.to_ical()
            try:
                logging.debug('Adding "{}"...'.format(todoIcal))
                calendar.add_todo(todoIcal)
                newItems += 1
            except Exception as e:
                logging.error('Error while adding {}: {}'.format(i['name'], e))
    logging.info('Pushed {} items to CalDAV'.format(newItems))

    # calendars = getcalendars()
    # for caldavcal in calendars:
    #     if caldavcal.canonical_url == url:
    #         for caldavtodo in caldavcal.todos(include_completed=True):
    #             cal = Calendar.from_ical(caldavtodo.data)
    #             for component in cal.walk('vtodo'):
    #                 uid = component['uid']
    #             try:
    #                 obj = nodebykey(data, 'caldav_uid', uid)
    #             except Exception:
    #                 obj = None
    #             if obj is None:
    #                 caldavtodo.delete()
    #                 delItems += 1
    #         logging.info('Deleted {} items on CalDAV'.format(delItems))

    #         for i in data:
    #             if i['cache_modified'] > lastsync:
    #                 todoIcal = TodoFromJSON(None, i).to_ical()
    #                 caldavcal.add_todo(todoIcal)
    #                 newItems += 1
    #         logging.info('Pushed {} items to CalDAV'.format(newItems))


if __name__ == '__main__':
    push()
