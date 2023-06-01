from event import Event
from config import Config
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from log import Log

class Spotify(object):
    player = "SPOTIFY"
    is_active = True
    is_playing = False
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
        self.is_playing = True
        self.__spotipy.start_playback(device_id=self.__device_id)
        self.__event.execute("spotify.music", True)

    def play(self):
        self.start()

    def pauze(self):
        self.is_playing = False
        self.__spotipy.pause_playback(device_id=self.__device_id)
        self.__event.execute("spotify.music", False)

    def play_pause(self, value = "toggle"):
        if (self.is_playing):
            self.pauze()
        else:
            self.play()

    def start_playlist(self, nr):
        playlist_id = self.__config.value["spotify_playlists"][str(nr)]
        self.__spotipy.start_playback(context_uri=f'spotify:playlist:{playlist_id}', device_id=self.__device_id)
        self.is_playing = True
        self.__event.execute("spotify.music", True)

    def on_play_stop(self, callback):
        self.__event.register("spotify.music", callback)

    def on_connection_change(self, callback):
        self.__event.register("spotify.connection", callback)

    def on_playlist_update(self, callback):
        self.__event.register("spotify.playlist_updated", callback)

    def on_playlist_add_item(self, callback):
        self.__event.register("spotify.playlist_add_item", callback)

    def on_playlist_remove_item(self, callback):
        self.__event.register("spotify.playlist_remove_item", callback)

    def on_playlist_clear(self, callback):
        self.__event.register("spotify.playlist_clear", callback)

    def cleanup(self):
        pass
