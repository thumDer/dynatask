import dynatask
from defaultconfig import configPath
import logging
from os import path


if __name__ == '__main__':
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('dynatask.log', 'w', 'utf-8')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s'))
    root_logger.addHandler(handler)

    if not path.exists(configPath):
        configError = (
            'Config file not found, please run'
            ' ./dynatask/defaultconfig.py to'
            ' deploy it, and fill the default settings manually'
            ' as per the documentation.'.format(configPath))
        print(configError)
        logging.error(configError)
        exit()

    logging.info('Started')
    print("Started")

    dynatask.run()

    logging.info('Finished')
    print("Finished")
