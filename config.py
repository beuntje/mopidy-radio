import configparser
import os

class Config(object):
    __config = False

    def __init__(self):
        self.__config = configparser.ConfigParser()
        self.__config.read(os.path.join(os.path.dirname(__file__), 'main.ini'))

    @property
    def value(self):
        return self.__config
