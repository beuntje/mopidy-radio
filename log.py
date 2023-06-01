
import datetime
from sys import argv

class Log(object):
  def __init__(self):
    pass

  def add(self, line, priority = "info"):
      if "no_{}".format(priority) in argv: return
      #if (priority =="socket"): return
      now = datetime.datetime.now()
      print ("{} - {} : {}".format(now.strftime("%Y-%m-%d %H:%M:%S"), priority, line))
