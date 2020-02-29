import configparser

config = configparser.ConfigParser()
defaultconfig = config
configPath = './dynatask/config.ini'

defaultconfig.read('./dynatask/defaultconfig.ini')

config.read(configPath)


def checkgroup(group):
    if group not in config:
        config[group] = {}


def checkitem(group, item, value):
    if item not in config[group]:
        config[group][item] = value


for group in defaultconfig:
    checkgroup(group)
    for item in defaultconfig[group]:
        value = defaultconfig[group][item]
        checkitem(group, item, value)


def updateconfig():
    with open(configPath, 'w') as configfile:
        config.write(configfile)
