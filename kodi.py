import configparser
import os
from event import Event 
from threading import Thread, Timer 
import websocket
import json
from log import Log 

# https://kodi.wiki/view/JSON-RPC_API/v8

class Kodi(object): 
  __volume = 30
  is_playing = False
  is_active = True
  __muted = False 
  __partymode = False
  __shuffled = False
  __repeat = "off" # off, one, all
  __player_id = 0
  __playlist_id = 0
  __log = Log()
  presets = []
  __socket_queued = []
  __socket_queue_busy = False
  __timers = {}
  __playlist_load_in_progress = False
  __ignore_methods = []; 

  def __init__(self):
    self.__log.add("init kodi", "kodi")
    config = configparser.ConfigParser()  
    config.read(os.path.join(os.path.dirname(__file__), 'kodi.ini'))
    self.__event = Event()
    self.__start_socket(config['Kodi']['host'], int(config['Kodi']['websocket']))
    self.presets = json.loads( config['Music']['presets'] )


  def __start_socket(self, host, port): 
    self.__log.add("start socket {}:{}".format(host, port), "socket")
    websocket.enableTrace(False)
    self.__socket = websocket.WebSocketApp("ws://{}:{}".format(host, port), on_message = self.__socket_message, on_open = self.__socket_open, on_error = self.__socket_error, on_close = self.__socket_close) 
    self.__socket_msg_id = 0
    self.__queue = {}
    thread = Thread(target=self.__socket.run_forever)
    thread.daemon = True
    thread.start()


  def __socket_message(self, msg): 
    try:  
      self.__log.add("new message: {}".format( msg ), "socket")
      event = json.loads(msg) 
      
      if "result" in event: 
        if event["id"] in self.__queue:  
          self.__queue[event["id"]](event["result"])
          del self.__queue[event["id"]]
      elif "error" in event: 
        if event["id"] in self.__queue:  
          self.__queue[event["id"]](event["error"])
          del self.__queue[event["id"]]

      if "method" in event:  
        if event["method"] in self.__ignore_methods: 
          self.__ignore_methods.remove(event["method"])
          return

        if event["method"] == "Application.OnVolumeChanged": 
          self.__volume = event["params"]["data"]["volume"]
          self.__muted = event["params"]["data"]["muted"]

        if event["method"] == "Player.OnPropertyChanged": 
          if "partymode" in event["params"]["data"]["property"]: self.__partymode = event["params"]["data"]["property"]["partymode"]
          if "shuffled" in event["params"]["data"]["property"]: self.__shuffled = event["params"]["data"]["property"]["shuffled"]
          if "repeat" in event["params"]["data"]["property"]: self.__repeat = event["params"]["data"]["property"]["repeat"]
 
        elif event["method"] in ["Player.OnPlay", "Player.OnResume"]: 
          self.__started_playing(True)
          
        elif event["method"] in ["Player.OnStop", "Player.OnPause"]: 
          self.__started_playing(False)
          
        elif event["method"] in ["Playlist.OnAdd", "Playlist.OnRemove"]:  
          if not self.__playlist_load_in_progress: self.__playlist_updated()
 
        elif event["method"] in ["Playlist.OnClear"]:  
          if not self.__playlist_load_in_progress: self.__event.execute("kodi.playlist_clear")
 
 
    except ValueError: 
      self.__log.add("error on msg", "socket")
      pass


  def __socket_error(self, msg): 
    pass


  def __socket_open(self): 
    self.__set_active(True) 

    def check_active_player(result): 
      if len(result) > 0: 
        self.__started_playing(True)
        self.__player_id = result[0]["playerid"]
        self.__socket_send("Player.GetProperties", {'playerid': self.__player_id, 'properties': ["partymode", "shuffled", "repeat"]}, set_player_properties)
      else: 
        self.__started_playing(False)

    def set_application_properties(result):  
      self.__volume = result["volume"]
      self.__muted = result["muted"] 
 
    def set_player_properties(result):   
      self.__partymode = result["partymode"] 
      self.__shuffled = result["shuffled"] 
      self.__repeat = result["repeat"] 

    self.__socket_send("Player.GetActivePlayers", {}, check_active_player)
    self.__socket_send("Application.GetProperties", {'properties': ["volume", "muted"]}, set_application_properties)
 
 
  def __playlist_updated(self): 
    def send_playlist(result): 
      if "items" in result: 
        self.__event.execute("kodi.playlist_updated", result["items"])

    def wait_until_stable():   
      self.__socket_send("Playlist.GetItems", {"playlistid": self.__playlist_id}, send_playlist)
      if "playlist_updated" in self.__timers: del self.__timers["playlist_updated"]
 
    if "playlist_updated" in self.__timers: 
      self.__timers["playlist_updated"].cancel() 
    self.__timers["playlist_updated"] = Timer(0.1, wait_until_stable) 
    self.__timers["playlist_updated"].start()   

  def __socket_close(self): 
    self.__set_active(False) 


  def __set_active(self, value): 
    self.__event.execute("kodi.connection", value)
    self.is_active = value
  

  def __socket_queue(self, method, params, callback = False): 
    def do_next(result): 
      self.__socket_queue_busy = True
      if len(self.__socket_queued)>0:
        next = self.__socket_queued.pop(0)
        if "execute" in next: next["execute"](result)
        self.__socket_send(next["method"], next["params"], do_next)
      else:  
        self.__socket_queue_busy = False 

    self.__socket_queued.append({"method": method, "params": params}) 
    if callback: 
      self.__socket_queued.append({"method": "JSONRPC.Ping", "params": {}, "execute": callback}) 

    if not self.__socket_queue_busy: do_next(0)
 

  def __socket_send(self, method, params, callback = False): 
    if self.is_active: 
      self.__socket_msg_id += 1 
      data = {
          'jsonrpc': '2.0',
          'id': self.__socket_msg_id,
          'method': method,
          'params': params
      }
      if callback: 
        self.__queue[self.__socket_msg_id] = callback

      self.__socket.send(json.dumps(data)) 
      self.__log.add("send msg {}: {}".format(self.__socket_msg_id , json.dumps(data)), "socket")
      return self.__socket_msg_id 

  @property
  def volume(self): 
    return self.__volume

  @volume.setter
  def volume(self, value): 
    if value < 0: value = 0
    if value > 100: value = 100
    self.__volume = value
    self.__socket_send("Application.SetVolume", {"volume":int(value)})
 

  @property
  def muted(self): 
    return self.__muted

  @muted.setter
  def muted(self, value): 
    self.__socket_send("Application.SetMute", {"mute": value})
 

  @property
  def shuffled(self): 
    return self.__shuffled

  @shuffled.setter 
  def shuffled(self, value): 
    self.__socket_send("Player.SetShuffle", {"playerid": self.__player_id, "shuffle": value})
 

  @property
  def repeat(self): 
    return self.__repeat

  @repeat.setter
  def repeat(self, value):
    self.__socket_send("Player.SetRepeat", {"playerid": self.__player_id, "repeat": value})
 

  @property
  def partymode(self): 
    return self.__partymode

  @partymode.setter
  def partymode(self, value):  
    self.__socket_send("Player.SetPartymode", {"playerid": self.__player_id, "partymode": value})
 

  def next(self):  
    self.__socket_send("Player.GoTo", [self.__player_id, "next"])

  def previous(self):  
    self.__socket_send("Player.GoTo", [self.__player_id, "previous"])

  def stop(self):   
    self.__socket_send("Player.Stop", [self.__player_id])

  def start(self):   
    self.__socket_send("Player.PlayPause", {"playerid": self.__player_id , "play": True}) 

  def pauze(self):   
    self.__socket_send("Player.PlayPause", {"playerid": self.__player_id , "play": False}) 

  def play_pause(self, value = "toggle"):   
    self.__socket_send("Player.PlayPause", {"playerid": self.__player_id , "play": value}) 

  def start_playlist(self, songs):
    def playlist_ready(value):
      self.__playlist_load_in_progress = False

    self.__playlist_load_in_progress = True
    self.__log.add("playlist wordt gestart")

    self.__ignore_methods.append("Playlist.OnClear")
    self.__socket_queue("Playlist.Clear", {"playlistid": self.__playlist_id})
    nr = 0
    for song in songs:
      self.__ignore_methods.append("Playlist.OnAdd")
      self.__socket_queue("Playlist.Add", {"playlistid": self.__playlist_id , "item": {"songid": song["id"]}})
      if nr == 0:
        self.__socket_queue("Player.Open", { "item":{"position":0,"playlistid":  self.__playlist_id },"options":{}  })
      nr += 1
    self.__socket_queue("JSONRPC.Ping", {}, playlist_ready)

  def on_play_stop(self, callback): 
    self.__event.register("kodi.music", callback)

  def on_connection_change(self, callback): 
    self.__event.register("kodi.connection", callback)

  def on_playlist_update(self, callback):   
    self.__event.register("kodi.playlist_updated", callback) 

  def on_playlist_clear(self, callback):  
    self.__event.register("kodi.playlist_clear", callback) 

  def __started_playing(self, value): 
    if value != self.is_playing: 
      self.__log.add("changed playing status to {}".format(value))
      self.is_playing = value
      self.__event.execute("kodi.music", value)

  def cleanup(self): 
    self.__socket.close() 
