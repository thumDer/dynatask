import json
from helper import nodebykey, complementdata, stamp
from datetime import datetime
from os import path

cachepath = './data/cache.json'


def savecache():
    with open(cachepath, 'w', encoding='utf-8') as create_file:
        json.dump(cache, create_file, ensure_ascii=False, indent=4)


def loadcache():
    with open(cachepath, 'r', encoding='utf-8') as read_file:
        return(json.load(read_file))


if not path.exists(cachepath):
    cache = {}
    cache['synced'] = 0
    cache['data'] = []

    savecache()
else:
    cache = loadcache()


def comparedynalist(data):
    loadcache()
    cachedids = [obj['dynalist_id'] for obj in cache['data']
                 if 'dynalist_id' in obj]
    ids = [obj['dynalist_id'] for obj in data]
    for node in data:
        if node['dynalist_id'] not in cachedids:
            node['cache_modified'] = stamp()
            cache['data'].append(node)
            print('{} added from Dynalist!'.format(node['name']))
        else:
            cachednode = nodebykey(
                cache['data'],
                'dynalist_id',
                node['dynalist_id'])
            if node['dynalist_modified'] > cache['synced']:
                for key in node:
                    cachednode[key] = node[key]
                cachednode['cache_modified'] = stamp()
                print('{} updated from Dynalist!'.format(cachednode['name']))

    updatedcachedata = []
    nodestodelete = []
    for cachednode in cache['data']:
        if 'dynalist_id' in cachednode:
            if cachednode['dynalist_id'] in ids:
                updatedcachedata.append(cachednode)
            else:
                print('{} deleted (Dynalist)!'.format(cachednode['name']))
                nodestodelete.append(cachednode)
        else:
            updatedcachedata.append(cachednode)
    cache['data'] = updatedcachedata

    savecache()
    return(cache['data'])


def comparecaldav(data):
    cacheduids = [obj['caldav_uid'] for obj in cache['data']
                  if 'caldav_uid' in obj]
    uids = [obj['caldav_uid'] for obj in data]
    loadcache()
    for node in data:
        if 'dynalist_id' not in node and node['caldav_uid'] not in cacheduids:
            node['cache_modified'] = stamp()
            cache['data'].append(node)
            print('{} added from caldav!'.format(node['name']))
        else:
            try:
                cachednode = nodebykey(
                    cache['data'],
                    'dynalist_id',
                    node['dynalist_id'])
                if node['caldav_modified'] > cache['synced'] \
                        or 'caldav_uid' not in cachednode:
                    for key in node:
                        cachednode[key] = node[key]
                    cachednode['cache_modified'] = stamp()
                    print('{} updated from caldav!'.format(cachednode['name']))
            except Exception:
                pass

    for uid in cacheduids:
        if uid not in uids:
            node = nodebykey(data, 'caldav_uid', uid)
            if 'dynalist_id' not in node:
                cache['data'].remove(node)

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
    return(cache['data'])


def updatetimestamp():
    cache['synced'] = stamp()
    savecache()


def timestamp():
    loadcache()
    return(cache['synced'])
