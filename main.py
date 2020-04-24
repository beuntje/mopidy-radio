from siera import Siera
from kodi import Kodi
from log import Log
from playlist import Playlist
from colors import Color as COLOR

def option_changed(button, value): 
    if (button == 2): MUSIC.shuffled = value
    if (button == 3): MUSIC.repeat = "all" if value else "off"
    if (button == 4): MUSIC.partymode = value
    

def preset_changed(preset): 
    if RADIO.option_is_down(0): 
        pass
    elif RADIO.option_is_down(1): 
        preset += 5
    else: 
        preset += 10

    MUSIC.start_playlist(PLAYLIST.load(preset)) 

def playlist_update(playlist):  
    if not MUSIC.partymode: 
        PLAYLIST.save(playlist)

def playlist_clear(): 
    PLAYLIST.new()    

def volume_turn(value): 
    MUSIC.volume += value 
    

def channel_turn(value): 
    if value > 0: 
        MUSIC.next()
    else: 
        MUSIC.previous()

def radio_on_off(is_on): 
    if is_on: 
        RADIO.background_led(COLOR.yellow + COLOR.yellow)
        RADIO.power_led(COLOR.green)
        RADIO.relais(0) 
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
    global PROGRAM_ACTIVE 
    PROGRAM_ACTIVE = False


LOG = Log() 

MUSIC = Kodi()
RADIO = Siera()
PLAYLIST = Playlist()
 
RADIO.on_preset_change(preset_changed) 
RADIO.on_option_change(option_changed)
RADIO.on_volume_turn(volume_turn) 
RADIO.on_channel_turn(channel_turn)
RADIO.on_stop(MUSIC.stop)
RADIO.on_reset(kill_all)
  
MUSIC.on_play_stop(radio_on_off)
connection_active(MUSIC.is_active)

MUSIC.on_connection_change(connection_active)
MUSIC.on_playlist_update(playlist_update)
MUSIC.on_playlist_clear(playlist_clear)

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
