from event import Event
from config import Config
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from log import Log

class Spotify(object):
    player = "SPOTIFY"
    __config = False
    __spotipy = False
    __log = Log()
    __device_id = False

    def __init__(self):
        self.__config = Config()
        self.__log.add("init spotify", "spotify")
        self.__event = Event()
        #self.__queue = {}
        self.__connect(self.__config.value['spotify']['client_id'], self.__config.value['spotify']['client_secret'], self.__config.value['spotify']['redirect_uri'])
        self.__device_id = self.__config.value['spotify']['device_id'];

    def __connect(self, client_id, client_secret, redirect_uri):
        auth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope="user-modify-playback-state,user-read-playback-state")
        print(auth.get_authorize_url())

        self.__spotipy = spotipy.Spotify(auth_manager=auth)


    @property
    def volume(self):
        return self.__spotipy.current_playback()['device']['volume_percent']

    @volume.setter
    def volume(self, value):
        if value < 0: value = 0
        if value > 100: value = 100
        self.__spotipy.volume(value, device_id=self.__device_id)

    def next(self):
        self.__spotipy.next_track(device_id=self.__device_id)

    def previous(self):
        self.__spotipy.previous_track(device_id=self.__device_id)

    def stop(self):
        self.pauze()

    def start(self):
        self.__spotipy.start_playback(device_id=self.__device_id)

    def play(self):
        self.start()

    def pauze(self):
        self.__spotipy.pause_playback(device_id=self.__device_id)

    def play_pause(self, value = "toggle"):
        print("todo")

    def start_playlist(self, songs):
        print (songs)

    def start_playlist(self, nr):
        playlist_id = self.__config.value["spotify_playlists"][str(nr)]
        self.__spotipy.start_playback(context_uri=f'spotify:playlist:{playlist_id}', device_id=self.__device_id)









"""

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
    self.__playlist_get()


    ####### PLAYLIST

    def __playlist_add(self, item):
    if not self.__playlist_load_in_progress: self.__event.execute("kodi.playlist_add_item", item)
    self.__playlist_updated()

    def __playlist_remove(self, position):
    item = self.__active_playlist.pop(position)
    if not self.__playlist_load_in_progress: self.__event.execute("kodi.playlist_remove_item", item)
    self.__playlist_updated()

    def __playlist_clear(self):
    if not self.__playlist_load_in_progress: self.__event.execute("kodi.playlist_clear")
    self.__playlist_updated()

    def __playlist_get(self, callback = False):
    def update_playlist(result):
      if "items" in result:
        self.__active_playlist = result["items"]
        if callback:
          callback(result["items"])
    self.__socket_send("Playlist.GetItems", {"playlistid": self.__playlist_id}, update_playlist)

    def __playlist_updated(self):
    def send_playlist(result):
      if not self.__playlist_load_in_progress: self.__event.execute("kodi.playlist_updated", result)

    def wait_until_stable():
      self.__playlist_get(send_playlist)
      if "playlist_updated" in self.__timers: del self.__timers["playlist_updated"]

    if "playlist_updated" in self.__timers:
      self.__timers["playlist_updated"].cancel()
    self.__timers["playlist_updated"] = Timer(0.1, wait_until_stable)
    self.__timers["playlist_updated"].start()



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

    def start_playlist(self, songs):
    def playlist_ready(value):
      self.__playlist_load_in_progress = False

    self.__playlist_load_in_progress = True
    self.__log.add("playlist wordt gestart")

    self.__socket_queue("Playlist.Clear", {"playlistid": self.__playlist_id})
    nr = 0
    for song in songs:
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

    def on_playlist_add_item(self, callback):
    self.__event.register("kodi.playlist_add_item", callback)

    def on_playlist_remove_item(self, callback):
    self.__event.register("kodi.playlist_remove_item", callback)


    def on_playlist_clear(self, callback):
    self.__event.register("kodi.playlist_clear", callback)

    def __started_playing(self, value):
    if value != self.is_playing:
      self.__log.add("changed playing status to {}".format(value))
      self.is_playing = value
      self.__event.execute("kodi.music", value)

    def cleanup(self):
    self.__socket.close()

"""
