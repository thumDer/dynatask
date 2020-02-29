import json
from helper import nodebykey, stamp
from os import path
import logging

cachepath = './data/cache.json'


def savecache():
    with open(cachepath, 'w', encoding='utf-8') as create_file:
        json.dump(cache, create_file, ensure_ascii=False, indent=4)


def loadcache():
    with open(cachepath, 'r', encoding='utf-8') as read_file:
        data = json.load(read_file)
        logging.info('Cache loaded, item count: {}'.format(len(data['data'])))
        return(data)


if not path.exists(cachepath):
    cache = {}
    cache['synced'] = 0
    cache['data'] = []

    savecache()
else:
    cache = loadcache()


def comparedynalist(data):
    loadcache()
    newItems = 0
    modItems = 0
    delItems = 0
    cachedids = [obj['dynalist_id'] for obj in cache['data']
                 if 'dynalist_id' in obj]
    ids = [obj['dynalist_id'] for obj in data]
    for node in data:
        logging.debug('Comparing {} from Dynalist'.format(node['name']))
        if node['dynalist_id'] not in cachedids:
            logging.debug('{} is new, adding to cache.'.format(node['name']))
            node['cache_modified'] = stamp()
            cache['data'].append(node)
            newItems += 1
        else:
            cachednode = nodebykey(
                cache['data'],
                'dynalist_id',
                node['dynalist_id'])
            if node['dynalist_modified'] > cache['synced']:
                logging.debug('{} is modified, '
                              'updating cache.'.format(node['name']))
                for key in node:
                    cachednode[key] = node[key]
                cachednode['cache_modified'] = stamp()
                modItems += 1

    updatedcachedata = []
    nodestodelete = []
    for cachednode in cache['data']:
        if 'dynalist_id' in cachednode:
            if cachednode['dynalist_id'] in ids:
                updatedcachedata.append(cachednode)
            else:
                logging.debug('{} not found, '
                              'removing from cache.'
                              .format(cachednode['name']))
                nodestodelete.append(cachednode)
                delItems += 1
        else:
            updatedcachedata.append(cachednode)
    cache['data'] = updatedcachedata

    savecache()
    logging.info('Dynalist compare results: New: {}, Modified: {}, '
                 'Deleted: {}'.format(newItems, modItems, delItems))
    return(cache['data'])


def comparecaldav(data):
    newItems = 0
    modItems = 0
    delItems = 0
    cacheduids = [obj['caldav_uid'] for obj in cache['data']
                  if 'caldav_uid' in obj]
    uids = [obj['caldav_uid'] for obj in data]
    loadcache()
    for node in data:
        logging.debug('Comparing {} from Caldav'.format(node['name']))
        if 'dynalist_id' not in node and node['caldav_uid'] not in cacheduids:
            logging.debug('{} is new, adding to cache.'.format(node['name']))
            node['cache_modified'] = stamp()
            cache['data'].append(node)
            newItems += 1
        else:
            try:
                cachednode = nodebykey(
                    cache['data'],
                    'dynalist_id',
                    node['dynalist_id'])
            except Exception as e:
                logging.error(
                    'Item: {}, Exception: {}'.format(node['name'], e))
                try:
                    cachednode = nodebykey(
                        cache['data'],
                        'caldav_uid',
                        node['caldav_uid'])
                    if node['caldav_modified'] > cache['synced'] \
                            or 'caldav_uid' not in cachednode:
                        logging.debug('{} is modified, '
                                      'updating cache.'.format(node['name']))
                        for key in node:
                            cachednode[key] = node[key]
                        cachednode['cache_modified'] = stamp()
                        modItems += 1
                except Exception as e:
                    logging.error(
                        'Item: {}, Exception: {}'.format(node['name'], e))

    for uid in cacheduids:
        if uid not in uids:
            node = nodebykey(data, 'caldav_uid', uid)
            if node is not None and'dynalist_id' not in node:
                logging.debug('{} not found, '
                              'removing from cache.'
                              .format(cachednode['name']))
                cache['data'].remove(node)
                delItems += 1

    # updatedcachedata = []
    # nodestodelete = []
    # for cachednode in cache['data']:
    #     if cachednode['dynalist_id'] in ids:
    #         updatedcachedata.append(cachednode)
    #     else:
    #         print('{} deleted!'.format(cachednode['name']))
    #         nodestodelete.append(cachednode)
    # cache['data'] = updatedcachedata

    savecache()
    logging.info('Caldav compare results: New: {}, Modified: {}, '
                 'Deleted: {}'.format(newItems, modItems, delItems))
    return(cache['data'])


def updatetimestamp():
    cache['synced'] = stamp()
    savecache()


def getsyncstamp():
    loadcache()
    return(cache['synced'])
