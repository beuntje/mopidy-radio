from spotify import Spotify
from config import Config

config = Config();
print(config.value['spotify']['client_id']);

MUSIC = Spotify()
print (MUSIC.volume)
MUSIC.volume += 1
MUSIC.volume += 1
MUSIC.volume += 1
MUSIC.volume += 1

while True:
    pass

exit()
print (MUSIC.volume)

# MUSIC.play()

print(MUSIC.player)
print(MUSIC.volume)

# MUSIC.start_playlist(2)

#MUSIC.debug()
MUSIC.start_playlist(1)
