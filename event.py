from log import Log


class Event:
  callbacks = {}
  __log = Log()

  def register(self, eventkey, func):
    if not eventkey in  self.callbacks: self.callbacks[eventkey] = []
    self.callbacks[eventkey].append( func )

  def execute(self, eventkey, *args):
    self.__log.add("event '{}' fired ({})".format(eventkey, args), "event")

    if eventkey in self.callbacks:
        for func in self.callbacks[eventkey]:
            if len(args) == 0:
                func()
            elif len(args) == 1:
                func(args[0])
            elif len(args) == 2:
                func(args[0], args[1])
            elif len(args) == 3:
                func(args[0], args[1], args[2])
            elif len(args) == 4:
                func(args[0], args[1], args[2], args[2])
            else:
                print ("event moet meer parameters ondersteunen")
                exit
