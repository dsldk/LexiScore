from configparser import ConfigParser
from os import sep
from os.path import dirname

LOCALPATH = dirname(__file__)
if LOCALPATH:
    LOCALPATH += sep
CONFIG = ConfigParser()
CONFIG.read(('%sdefault.ini' % (LOCALPATH,),
             '%sconfig.ini' % (LOCALPATH,)))