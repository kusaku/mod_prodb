import functools
import uuid

from ProDB import logger


@functools.lru_cache()
def getRoundKeyByPlayerCIDs_mock(*cids):
    result = str(uuid.uuid4())
    logger.debug('[mock] getRoundKeyByPlayerCIDs [ {} ] = {}'.format(', '.join(cids), result))
    return result


@functools.lru_cache()
def getTeamKeyByPlayerCIDs_mock(*cids):
    result = str(uuid.uuid4())
    logger.debug('[mock] getTeamKeyByPlayerCIDs [ {} ] = {}'.format(', '.join(cids), result))
    return result


@functools.lru_cache()
def getTeamNameByPlayerCIDs_mock(*cids):
    result = str(uuid.uuid4())
    logger.debug('[mock] getTeamNameByPlayerCIDs [ {} ] = {}'.format(', '.join(cids), result))
    return result


@functools.lru_cache()
def getPlayerKeyByPlayerCID_mock(cid):
    result = str(uuid.uuid4())
    logger.debug('[mock] getPlayerKeyByPlayerCID {} = {}'.format(cid, result))
    return result
