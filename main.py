from siera import Siera
from kodi import Kodi
from log import Log
from playlist import Playlist
from config import Config
from colors import Color as COLOR
import os

def option_changed(button, value):
    if (button == 2): MUSIC.shuffled = value
    if (button == 3): MUSIC.repeat = "all" if value else "off"
    if (button == 4): MUSIC.partymode = value

def get_preset():
    preset = RADIO.selected_preset()
    if preset == 0:
        return 0
    if RADIO.option_is_down(0):
        pass
    elif RADIO.option_is_down(1):
        preset += 5
    else:
        preset += 10
    return preset


def preset_changed(preset):
    preset = get_preset()

    if (PLAYLIST.current == preset):
        MUSIC.play()
    else:
        if (MUSIC.player == "KODI"):
            MUSIC.start_playlist(PLAYLIST.load(preset))
        else:
            MUSIC.start_playlist(preset)

def stop_music():
	MUSIC.pauze()

def playlist_update(playlist):
    if not MUSIC.partymode:
        if get_preset() == PLAYLIST.current:
            PLAYLIST.save(playlist)


def volume_turn(value):
    MUSIC.volume += value


def channel_turn(value):
    if value > 0:
        MUSIC.next()
        pass
    else:
        MUSIC.previous()
        pass

def radio_on_off(is_on):
    if is_on:
        RADIO.background_led(COLOR.yellow + COLOR.yellow)
        RADIO.relais(0)
        if PLAYLIST.custom():
            RADIO.power_led(COLOR.green)
        else:
            RADIO.power_led(COLOR.yellow)
    else:
        RADIO.background_led(COLOR.black + COLOR.black)
        RADIO.power_led(COLOR.orange)
        RADIO.relais(1)


def connection_active(is_active):
    if is_active:
        radio_on_off(MUSIC.is_playing)
    else:
        RADIO.background_led(COLOR.red + COLOR.red)
        RADIO.power_led(COLOR.red)

def kill_all():
    LOG.add("reboot system by hardware clickclickclickclickclick")
    os.system('sudo shutdown -r now')

def kill_program():
    global PROGRAM_ACTIVE
    PROGRAM_ACTIVE = False

def get_player():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'main.ini'))
    self.__event = Event()
    #self.__queue = {}
    self.__connect(config['Spotify']['CLIENT_ID'], config['Spotify']['CLIENT_SECRET'], config['Spotify']['REDIRECT_URI'])


LOG = Log()
CONFIG = Config()

if CONFIG.value['main']['player'] == "spotify":
    MUSIC = Spotify()
elif CONFIG.value['main']['player'] == "kodi":
    MUSIC = Kodi()
else:
    print("Main player not set")
    exit()

RADIO = Siera()
PLAYLIST = Playlist()

RADIO.on_preset_change(preset_changed)
RADIO.on_option_change(option_changed)
RADIO.on_volume_turn(volume_turn)
RADIO.on_channel_turn(channel_turn)
RADIO.on_stop(stop_music)
RADIO.on_option_5clicks(2, kill_program)
RADIO.on_option_5clicks(3, kill_all)

MUSIC.on_play_stop(radio_on_off)
connection_active(MUSIC.is_active)

MUSIC.on_connection_change(connection_active)
MUSIC.on_playlist_update(playlist_update)

PROGRAM_ACTIVE = True
try:
    LOG.add("started program", "main")
    while PROGRAM_ACTIVE:
        pass

except KeyboardInterrupt:
    PROGRAM_ACTIVE = False
    RADIO.cleanup()
    MUSIC.cleanup()

    LOG.add("stopped program",  "main")
