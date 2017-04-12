import functools
import random
import time
import uuid

from .Logger import Logger


@functools.lru_cache()
def getRoundKeyByPlayerCIDs_mock(*cids):
    time.sleep(0.0)
    result = str(uuid.uuid4())
    Logger.debug('[mock] getRoundKeyByPlayerCIDs [ {} ] = {}'.format(', '.join(cids), result))
    return result


@functools.lru_cache()
def getTeamKeyByPlayerCIDs_mock(*cids):
    time.sleep(random.random())
    result = str(uuid.uuid4())
    Logger.debug('[mock] getTeamKeyByPlayerCIDs [ {} ] = {}'.format(', '.join(cids), result))
    return result


@functools.lru_cache()
def getTeamNameByPlayerCIDs_mock(*cids):
    time.sleep(random.random())
    result = str(uuid.uuid4())
    Logger.debug('[mock] getTeamNameByPlayerCIDs [ {} ] = {}'.format(', '.join(cids), result))
    return result


@functools.lru_cache()
def getPlayerKeyByPlayerCID_mock(cid):
    time.sleep(random.random())
    result = str(uuid.uuid4())
    Logger.debug('[mock] getPlayerKeyByPlayerCID {} = {}'.format(cid, result))
    return result


def cache_clear_all():
    getRoundKeyByPlayerCIDs_mock.cache_clear()
    getTeamKeyByPlayerCIDs_mock.cache_clear()
    getTeamNameByPlayerCIDs_mock.cache_clear()
    getPlayerKeyByPlayerCID_mock.cache_clear()
    Logger.debug('Mock data caches are cleared')


def cache_info_all():
    return {
        'getRoundKeyByPlayerCIDs_mock': getRoundKeyByPlayerCIDs_mock.cache_info(),
        'getTeamKeyByPlayerCIDs_mock': getTeamKeyByPlayerCIDs_mock.cache_info(),
        'getTeamNameByPlayerCIDs_mock': getTeamNameByPlayerCIDs_mock.cache_info(),
        'getPlayerKeyByPlayerCID_mock': getPlayerKeyByPlayerCID_mock.cache_info(),
    }
