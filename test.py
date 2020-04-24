
from playlist import Playlist
from kodi import Kodi

def playlist_update(pllist): 
    print "playlist update"
    print pllist 
    PLAYLIST.save(pllist)
    pass

def playlist_clear(): 
    print "playlist clear"
    PLAYLIST.new()
    pass

def start(v): 
    pl = PLAYLIST.load(1)
    MUSIC.start_playlist(pl) 


PLAYLIST = Playlist()
MUSIC = Kodi()


MUSIC.on_connection_change(start)

MUSIC.on_playlist_update(playlist_update)
MUSIC.on_playlist_clear(playlist_clear)

PROGRAM_ACTIVE = True
try:
    while PROGRAM_ACTIVE:
        pass

except KeyboardInterrupt:
    PROGRAM_ACTIVE = False
    MUSIC.cleanup()
