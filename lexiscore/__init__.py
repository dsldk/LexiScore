import asyncio
import logging

# import time
from collections import OrderedDict
from configparser import RawConfigParser
from functools import wraps
from os import sep, environ
from os.path import dirname
from typing import Any, Callable


class MultiOrderedDict(OrderedDict):
    """ConfigParser that allows multiple entries with same name.

    Ex. print config.get("exif",  "extension")
    ['pdo.so', 'pdo_sqlite.so', 'pdo_mysql.so']
    Based on https://pastebin.com/cZ8SzbXK
    """

    def __setitem__(self, key, value):
        """Allow for multiple entries with same name, using [] notation."""
        if key.endswith("[]"):
            key = key[:-2]
            if isinstance(value, list) and key in self:
                self[key].extend(value)
            else:
                super(OrderedDict, self).__setitem__(key, value)
        else:
            super(MultiOrderedDict, self).__setitem__(key, value)


LOCALPATH = dirname(__file__)
if LOCALPATH:
    LOCALPATH += sep
CONFIG = RawConfigParser(dict_type=MultiOrderedDict, strict=False)
CONFIG.read(("%sdefault.ini" % (LOCALPATH,), "%sconfig.ini" % (LOCALPATH,)))

log_level = environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(format="%(asctime)s : %(levelname)s : %(message)s", level=log_level)
logger = logging.getLogger(__name__)


def async_timeit(func):
    """Async function decorator to time execution. Must be used with awaited functions."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = asyncio.get_event_loop().time()
        result = await func(*args, **kwargs)
        end = asyncio.get_event_loop().time()
        logger.info(f"{func.__name__} took {end - start:.6f} seconds to complete")
        return result

    return wrapper
