import dyntocal
import logging

if __name__ == '__main__':
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('dyntocal.log', 'w', 'utf-8')
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(message)s'))
    root_logger.addHandler(handler)
    logging.info('Started')
    print("Started")

    dyntocal.run()

    logging.info('Finished')
    print("Finished")
