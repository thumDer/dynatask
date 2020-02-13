from __future__ import print_function
import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import config
import logging
import datetime


def pushtogoogle(dynEvents):
    logging.info("Connecting to Google.")
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    tokenPath = os.path.join(os.path.dirname(__file__), 'token.pickle')
    logging.debug("Token Path: {}".format(tokenPath))
    if os.path.exists(tokenPath):
        with open(tokenPath, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            logging.debug("Refreshing Credentials.")
        else:
            logging.debug("Can't refresh token, asking for login.")
            flow = InstalledAppFlow.from_client_secrets_file(
                'dynalist_cred.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            logging.debug("Token saved.")

    service = build('calendar', 'v3', credentials=creds)

    # get events from calendar
    logging.debug("Polling events.")
    existingEvents = []
    page_token = None
    while True:
        events = service.events().list(
            calendarId=config.dlCalId, pageToken=page_token).execute()
        for event in events['items']:
            existingEvents.append(event['id'])
        page_token = events.get('nextPageToken')
        if not page_token:
            break

    # delete existing events
    logging.info(str.format("Events to delete: {0}", len(existingEvents)))
    try:
        if existingEvents:
            for e in existingEvents:
                service.events().delete(
                    calendarId=config.dlCalId, eventId=e).execute()
        logging.debug("Events deleted.")
    except Exception as e:
        logging.debug(str(e))

    logging.debug("Incoming data: {}".format(dynEvents))
    logging.info("Events to create: {}".format(len(dynEvents)))
    success = 0
    for n in dynEvents:
        try:
            if n.allday:
                dateKey = 'date'
                startDate = n.date.strftime('%Y-%m-%d')
                endDate = startDate
            else:
                dateKey = 'dateTime'
                startDate = n.date.strftime('%Y-%m-%dT%H:%M:%SZ')
                endDate = (n.date + datetime.timedelta(minutes=60)).strftime(
                    '%Y-%m-%dT%H:%M:%SZ')

            if n.alarm == "":
                reminder = ""
            else:
                reminder = {
                    'useDefault': False,
                    'overrides': [
                        {
                            'method': 'popup',
                            'minutes': n.alarm
                        },
                    ],
                },

            event = {
                'summary': n.name,
                'description': n.description,
                'start': {
                    dateKey: startDate,
                    'timeZone': 'Europe/Budapest'
                },
                'end': {
                    dateKey: endDate,
                    'timeZone': 'Europe/Budapest'
                },
                'reminders': reminder,
                'transparency': 'transparent',
                'source.title': 'Dynalist',
                'source.url': 'https://dynalist.io/'
            }
            logging.debug(event)
            service.events().insert(
                calendarId=config.dlCalId, body=event).execute()
            logging.debug("Event created: {}".format(event.get('summary')))
            success += 1
        except Exception as e:
            logging.debug("Event: {}\n{}".format(n.name, e))
    logging.info("Successfully created {} events".format(success))
