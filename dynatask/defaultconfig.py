import configparser
from os import path

config = configparser.ConfigParser()
configPath = './dynatask/config.ini'

config['dynalist'] = {'file_url': 'https://dynalist.io/api/v1/file/list',
                      'doc_url': 'https://dynalist.io/api/v1/doc/read',
                      'api_key': '',
                      'tasklist_tag': '#tlist',
                      'task_tag': '#task',
                      'alarm_prefix': '#alarm'}

config['google'] = {'task_url': '',
                    'calendar_url': ''}

config['caldav'] = {'task_url': '',
                    'calendar_url': '',
                    'user': '',
                    'password': ''}


def deploy():
    with open(configPath, 'w') as configfile:
        config.write(configfile)


if __name__ == '__main__':
    if not path.exists(configPath):
        deploy()
        print('Config file created at {}'.format(configPath))
    else:
        print(
            'Found existing config file at {}, '
            'please remove it before deploying a new one.'
            .format(configPath))
