from __future__ import print_function
import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def pushtogoogle(events):
    dlCalId = '5h3iq4ee5tci4fgaovo5dd76d4@group.calendar.google.com'
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.


    tokenPath = os.path.join(os.path.dirname(__file__), 'token.pickle')
    if os.path.exists(tokenPath):
        with open(tokenPath, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'dynalist_cred.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # with open(tokenPath, 'rb') as token:
    #     creds = pickle.load(token)

    service = build('calendar', 'v3', credentials=creds)

    # get events from calendar
    existingEvents = []
    page_token = None
    while True:
        events = service.events().list(calendarId=dlCalId, pageToken=page_token).execute()
        for event in events['items']:
            existingEvents.append(event['id'])
        page_token = events.get('nextPageToken')
        if not page_token:
            break

    # delete existing events
    print(str.format("Events to delete: {0}", len(existingEvents)))
    if existingEvents:
        for e in existingEvents:
            service.events().delete(calendarId = dlCalId, eventId = e).execute()

    for n in events:
        event = {
            'summary': n.name,
            'description': n.description,
            'start': {
                'date': n.date.strftime('%Y-%m-%d'),
                'timeZone': 'Europe/Budapest'
            },
            'end': {
                'date': n.date.strftime('%Y-%m-%d'),
                'timeZone': 'Europe/Budapest'
            },
            'transparency': 'transparent',
            'source.title': 'Dynalist',
            'source.url': 'https://dynalist.io/'
        }
        # print(event)
        service.events().insert(calendarId = dlCalId, body = event).execute()
        print(str.format("Event created: {0}", event.get('summary')).encode('utf-8'))