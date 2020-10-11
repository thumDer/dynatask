from modules import dynalistconnector
from modules import caldavconnector
from modules import cache
from modules.defaultconfig import configPath, updateconfig
import logging
from os import path


if __name__ == '__main__':
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    handler = logging.FileHandler('dynatask.log', 'w', 'utf-8')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s'))
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    # root_logger.addHandler(console)

    if not path.exists(configPath):
        updateconfig()
        configError = (
            'Deployed default config to {}, '
            'please fill in user data.'.format(configPath))
        print(configError)
        logging.error(configError)
        exit()

    updateconfig()

    logging.info('Started')

    dynalistData = dynalistconnector.pull()

    caldavData = caldavconnector.pull()

    cache.comparecaldav(caldavData)

    cache.comparedynalist(dynalistData)

    cache.checkparents()

    caldavconnector.push(cache.loadcache())

    cache.updatetimestamp()

    logging.info('Finished')
