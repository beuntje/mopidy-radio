from spotify import Spotify
from config import Config

config = Config();
print(config.value['spotify']['client_id']);

MUSIC = Spotify()
print (MUSIC.volume)
#MUSIC.volume += 5
print (MUSIC.volume)

MUSIC.play()

print(MUSIC.player)

MUSIC.start_playlist(2)
