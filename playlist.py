import configparser
import os
import json
from log import Log
from config import Config

class Playlist(object):
  __path = False
  __id = False
  __log = Log()

  def __init__(self):
    config = Config()
    self.__path = config.value['Music']['location']

  def save(self, playlist):
    if self.__id:
      print ("DO SAVE AS {}".format(self.__id))
      with open(self.__filename(self.__id), 'w') as file:
        file.write(json.dumps(playlist))
        self.__log.add("save playlist", "playlist")
    else:
      print ("NO SAVE")

  def load(self, nr):
    self.__id = nr
    filename = self.__filename(nr)
    if os.path.exists(filename):
      with open(filename, 'r') as file:
        saved = json.loads(file.read())
        return saved

    else:
      self.__log.add("playlist {} does not exist".format(nr), "playlist")
      return []

  @property
  def current(self):
    return self.__id


  def new(self):
    self.__id = False
    pass

  def custom(self):
    return not self.__id

  def __filename(self, nr):
      return "{}/playlist_{}.txt".format(self.__path, nr)
