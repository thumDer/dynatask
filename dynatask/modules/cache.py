import json
from .helper import nodebykey, stamp
from os import path
import logging

cachepath = './data/cache.json'


def savecache(cache):
    with open(cachepath, 'w', encoding='utf-8') as create_file:
        json.dump(cache, create_file, ensure_ascii=False, indent=4)
        logging.info('Saved {} items to cache...'.format(len(cache['data'])))


def loadcache():
    with open(cachepath, 'r', encoding='utf-8') as read_file:
        data = json.load(read_file)
        logging.info('Loaded {} items from cache...'.format(len(data['data'])))
        return(data)


if not path.exists(cachepath):
    logging.info('No cache present, deploying...')
    cache = {}
    cache['synced'] = 0
    cache['data'] = []

    savecache(cache)
else:
    logging.info('Cache found, loading...')
    cache = loadcache()


def comparedynalist(data):
    logging.info('Comparing Dynalist data to cache...')
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
            logging.info('{} is new, adding to cache.'.format(node['name']))
            node['caldav_uid'] = node['dynalist_id']+'@dynatask'
            node['cache_modified'] = stamp()
            cache['data'].append(node)
            newItems += 1
        else:
            cachednode = nodebykey(
                cache['data'],
                'dynalist_id',
                node['dynalist_id'])
            if node['dynalist_modified'] > cache['synced']:
                logging.info('{} is modified, '
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
                logging.info('{} not found, '
                             'removing from cache.'
                             .format(cachednode['name']))
                nodestodelete.append(cachednode)
                delItems += 1
        else:
            updatedcachedata.append(cachednode)
    cache['data'] = updatedcachedata

    logging.info('Dynalist compare results: New: {}, Modified: {}, '
                 'Deleted: {}'.format(newItems, modItems, delItems))
    savecache(cache)


def comparecaldav(data):
    logging.info('Comparing CalDAV data to cache...')
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
            continue
            # logging.info('{} is new, adding to cache.'.format(node['name']))
            # node['cache_modified'] = stamp()
            # cache['data'].append(node)
            # newItems += 1
        else:
            if 'dynalist_id' in node:
                cachednode = nodebykey(
                    cache['data'],
                    'dynalist_id',
                    node['dynalist_id'])
            elif 'caldav_uid' in node:
                cachednode = nodebykey(
                    cache['data'],
                    'caldav_uid',
                    node['caldav_uid'])
            if cachednode is not None:
                if 'caldav_modified' in node:
                    modkey = 'caldav_modified'
                elif 'caldav_dtstamp' in node:
                    modkey = 'caldav_dtstamp'
                else:
                    modkey = ''
                if modkey != '':
                    if node[modkey] > cache['synced'] \
                            or 'caldav_uid' not in cachednode:
                        logging.info('{} is modified, '
                                     'updating cache.'.format(node['name']))
                        for key in node:
                            cachednode[key] = node[key]
                        cachednode['cache_modified'] = stamp()
                        modItems += 1

    for uid in cacheduids:
        if uid not in uids:
            node = nodebykey(data, 'caldav_uid', uid)
            if node is not None and'dynalist_id' not in node:
                logging.info('{} not found, '
                             'removing from cache.'
                             .format(cachednode['name']))
                cache['data'].remove(node)
                delItems += 1

    logging.info('CalDAV compare results: New: {}, Modified: {}, '
                 'Deleted: {}'.format(newItems, modItems, delItems))
    savecache(cache)
    return(cache['data'])


def checkparents():
    logging.info('Checking parents...')
    cache = loadcache()
    updatedcachedata = []
    count = 0
    for node in cache['data']:
        update = False
        if 'dynalist_parent_id' not in node:
            updatedcachedata.append(node)
            continue
        parentid = node['dynalist_parent_id']
        parentnode = nodebykey(cache['data'], 'dynalist_id', parentid)
        if parentnode is not None and 'caldav_uid' in parentnode:
            if 'caldav_parent' not in node:
                update = True
            elif node['caldav_parent'] != parentnode['caldav_uid']:
                update = True
        if update:
            node['caldav_parent'] = parentnode['caldav_uid']
            logging.info(
                'Updating relationship for "{}"'.format(node['name']))
            node['cache_modified'] = stamp()
            count += 1
        updatedcachedata.append(node)
    cache['data'] = updatedcachedata

    logging.info('Parent updated for {} of {} items!'.format(
        count, len(updatedcachedata)))
    savecache(cache)


def updatetimestamp():
    cache = loadcache()
    logging.info('Updating cache timestamp...')
    cache['synced'] = stamp()
    savecache(cache)


if __name__ == '__main__':
    checkparents()
