import dynalistconnector
import caldavconnector
import cache
from defaultconfig import configPath, updateconfig
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
        updateconfig()
        configError = (
            'Deployed default config to {}, '
            'please fill in user data.'.format(configPath))
        print(configError)
        logging.error(configError)
        exit()

    updateconfig()

    logging.info('Started')
    print("Started")

    dynalistData = dynalistconnector.pull()

    caldavData = caldavconnector.pull()

    cache.comparecaldav(caldavData)

    results = cache.comparedynalist(dynalistData)

    caldavconnector.push(results)

    cache.updatetimestamp()

    logging.info('Finished')
    print("Finished")
