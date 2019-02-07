import websocket
import json
from threading import Timer, Thread
from gpiozero import Button, LED, OutputDevice
import datetime
import time
import subprocess
import os

def on_message(ws, message): 
    global timerOnOff, queue, random
    event = json.loads(message)
    try: 
        if "event" in event: 
            if event['event'] == 'playback_state_changed':
                timerOnOff.cancel() 
                timerOnOff = Timer(0.5, stoppedPlaying)
                if event['new_state'] == 'playing': 
                    startedPlaying()
                elif event['new_state'] == 'stopped':
                    timerOnOff.start()  
            elif event['event'] == 'options_changed': 
                queue[sendCommand("core.tracklist.get_random", {})] = "random"
            else: 
                #print event
                pass
        elif "id" in event: 
            if event["id"] in queue: 
                if (queue[event["id"]] == "random"):  
                    random = event["result"]
                queue.pop(event["id"], None)
    except:
        log("An exception occurred: %s" % event)  

def stoppedPlaying(): # websocket meldt dat audio al sinds halve seconde gestopt is 
    setPlaying(False)

def startedPlaying(): # websocket meldt dat autdio gestart is
    setPlaying(True)

def setPlaying(value): 
    global playing
    if (playing != value): 
        playing = value 
        if (playing): 
            log ("started playing") 
            ledBottom(True, True, False) # geel
            powerBoxen(True)
        else: 
            log ("stopped playing") 
            ledBottom(False, False, False) # uit
            powerBoxen(False)

def startPlaylist(playlist): # het effectief starten van de playlist 
    global activePreset
    if activePreset != playlist: 
        activePreset = playlist
        shell("mpc consume off")
        shells(["mpc stop", "mpc clear", "mpc load %s" % playlist, "mpc play"])
        log ("load playlist %s" % playlist)
    else: 
        shell("mpc play")
        log ("continue play playlist %s" % playlist)

def stopPlayer(): 
    shell("mpc stop")

def volume_a_rising():
    if volume_b.is_pressed: 
        volumeTurn(2)
        #shell("mpc volume +2")

def volume_b_rising():
    if volume_a.is_pressed:  
        #shell("mpc volume -2")
        volumeTurn(-2)

def zender_a_rising(): 
    if zender_b.is_pressed:
        #shell("mpc next")
        zenderTurn(1)

def zender_b_rising():
    if zender_a.is_pressed:
        #shell("mpc prev")
        zenderTurn(-1)

def zenderTurn(value): 
    global nextPrev, timerZender
    if (not nextPrev): # net gestart met draaien of net doChangeZender gehandled
        timerZender.cancel() 
        timerZender = Timer(0.5, doChangeZender) 
        timerZender.start()
        nextPrev = 0
    nextPrev = nextPrev + value

def doChangeZender(): 
    global nextPrev 
    if (nextPrev > 0): 
        shell("mpc next")
    elif (nextPrev < 0): 
        shell("mpc prev")
    nextPrev = None

    
def volumeTurn(value): 
    global volumeChangeValue, timerVolume
    if (not volumeChangeValue): # net gestart met draaien of net doChangeVolume gehandled
        timerVolume.cancel() 
        timerVolume = Timer(0.3, doChangeVolume) 
        timerVolume.start()
        volumeChangeValue = 0
    volumeChangeValue = volumeChangeValue + value

def doChangeVolume(): 
    global volumeChangeValue, volume 
    volume = volume + volumeChangeValue
    if (volume > 100): 
        volume = 100
    if (volume < 0): 
        volume = 0
    shell("amixer set PCM -- %s%%" % volume)
    volumeChangeValue = None

    # if (volumeChangeValue > 0):  
    #    # shell("mpc volume +%s" % volumeChangeValue)
    #    #shell("amixer set PCM -- $[$(amixer get PCM|grep -o [0-9]*%%|sed 's/%%//')+%s]%%" % volumeChangeValue)
    #    #shell("amixer set PCM -- $[$(amixer get PCM|grep -o [0-9]*%%|sed 's/%%//')+%s]%%" % volumeChangeValue)
    #    shell("amixer set PCM -- %s%%" % volume)
        
    #elif (volumeChangeValue < 0): 
    #    # shell("mpc volume %s" % volumeChangeValue)
    #    #shell("amixer set PCM -- $[$(amixer get PCM|grep -o [0-9]*%%|sed 's/%%//')%s]%%" % volumeChangeValue)
    #    shell("amixer set PCM -- %s%%" % volume)


def changePlaylist(): 
    global timerPlaylist
    timerPlaylist.cancel() 
    timerPlaylist = Timer(0.5, checkPlaylist)
    timerPlaylist.start() 

def checkPlaylist():
    global presets
    preset = 0
    if top4.is_pressed: 
        preset = 5
    if top5.is_pressed: 
        preset = 10

    if channel1.is_pressed: # knop 1
        log ("knop 1 pressed")
        startPlaylist(presets[preset+0]) 
    elif channel3.is_pressed: # knop 3
        log ("knop 3 pressed")
        startPlaylist(presets[preset+2])
    elif channel4.is_pressed: # knop 4
        log ("knop 4 pressed")
        startPlaylist(presets[preset+3])
    elif channel5.is_pressed: # knop 5
        log ("knop 5 pressed")
        startPlaylist(presets[preset+4])
    elif channel0.is_pressed: # knop 2
        log ("knop 2 pressed")
        startPlaylist(presets[preset+1])
    else:
        log ("stop-knop pressed")
        stopPlayer()


def sendCommand(method, params): 
    global msgId 
    msgId += 1
    data = {
        'jsonrpc': '2.0',
        'id': msgId,
        'method': method,
        'params': params
    }
    ws.send(json.dumps(data)) 
    return msgId 
 
def setRepeatAndRandom(): 
    if top1.is_pressed: # 1e knop ingedrukt
        shell("mpc single off") 
        shell("mpc repeat off") 
        shell("mpc random on")
    elif not top2.is_pressed: #2e knop ingedrukt
        shell("mpc single off") 
        shell("mpc repeat on") 
        shell("mpc random on")
    else:  # geen knoppen ingedrukt
        shell("mpc single off") 
        shell("mpc repeat off") 
        shell("mpc random off")

def shell(command): 
    log ("shell %s" % command) 
    proc = subprocess.Popen(command, shell=True)
    
def shells(commands): 
    for c in commands: 
        log ("shell %s" % c) 
        proc = subprocess.Popen(c, shell=True)
        if proc.wait() != 0:
            log("There was an error (in shell)")
     
def on_open(ws):
    global activePreset
    log ("websocket open")
    setRepeatAndRandom()
    checkMount()
    ledTop(False, True, False) # groen
    ledBottom(False, False, False) # uit
    activePreset = None # reset presets 
    volumeTurn(0)

def checkMount(): 
    if (not os.path.isdir("/music/Network/A")): 
        shell("sh /root/mount.sh") 


def log(line): 
    global logFile
    now = datetime.datetime.now()
    path = "/root/logs/recent.log"

    if (not logFile): 
        if (now.year > 1970): 
            logFile = ("/root/logs/%d-%d-%d.log" % (now.year, now.month, now.day))
            proc = subprocess.Popen(("mv %s %s" % (path, logFile)), shell=True)
            if proc.wait() != 0:
                pass 
            path = logFile 
    else: 
        path = logFile 

    fullLine = "%d/%d %d:%d.%d - %s" % (now.day, now.month, now.hour, now.minute, now.second, line)
    proc = subprocess.Popen("echo \"%s\" >> %s" % (fullLine, path), shell=True) # geen shell, want anders infinite loop
    print(fullLine)

def powerBoxen(on): 
    if (on): 
        relais.on()
    else: 
        relais.off()

def ping(): 
    global timerPing
    log("ping")
    timerPing.cancel()
    timerPing = Timer(6 * 60 * 60, ping) # 6 uur
    timerPing.start()

def ledTop(red, green, blue): 
    if (red):
        ledTopRed.on()
    else: 
        ledTopRed.off()
    if (green):
        ledTopGreen.on()
    else: 
        ledTopGreen.off()
    if (blue):
        ledTopBlue.on()
    else: 
        ledTopBlue.off()


def ledBottom(red, green, blue): 
    if (red):
        ledBottomLeftRed.on()
        ledBottomRightRed.on()
    else: 
        ledBottomLeftRed.off()
        ledBottomRightRed.off()
    if (green):
        ledBottomLeftGreen.on()
        ledBottomRightGreen.on()
    else: 
        ledBottomLeftGreen.off()
        ledBottomRightGreen.off()
    if (blue):
        ledBottomLeftBlue.on()
        ledBottomRightBlue.on()
    else: 
        ledBottomLeftBlue.off()
        ledBottomRightBlue.off()


if __name__ == "__main__":
    logFile = None
    log ("started script")
    
    volume_a = Button(6, pull_up=True) # Rotary encoder pin A connected to GPIO 6
    volume_b = Button(12, pull_up=True) # Rotary encoder pin B connected to GPIO 12
    zender_a = Button(11, pull_up=True) # Rotary encoder pin A connected to GPIO 11
    zender_b = Button(8, pull_up=True) # Rotary encoder pin B connected to GPIO 8

    channel0 = Button(14, pull_up=True) # GPIO 14
    channel1 = Button(15, pull_up=True) # GPIO 15
    channel3 = Button(4, pull_up=True) # GPIO 4
    channel4 = Button(2, pull_up=True) # GPIO 2
    channel5 = Button(3, pull_up=True) # GPIO 3
    
    top1 = Button(22, pull_up=True) # GPIO
    top2 = Button(24, pull_up=True) # GPIO
    top3 = Button(23, pull_up=True) # GPIO
    top4 = Button(27, pull_up=True) # GPIO
    top5 = Button(17, pull_up=True) # GPIO
    

    ledTopRed = LED(25) #GPIO 25
    ledTopGreen = LED(7) #GPIO 7
    ledTopBlue = LED(18) #GPIO 18

    ledBottomRightRed = LED(20) #GPIO 20
    ledBottomRightGreen = LED(21) #GPIO 21
    ledBottomRightBlue = LED(26) #GPIO 26

    ledBottomLeftRed = LED(9) #GPIO 10
    ledBottomLeftGreen = LED(5) #GPIO 9
    ledBottomLeftBlue = LED(10) #GPIO 5

    relais = OutputDevice(13, active_high=False, initial_value=False) #GPIO 13

    volume_a.when_pressed = volume_a_rising 
    volume_b.when_pressed = volume_b_rising 
    zender_a.when_pressed = zender_a_rising 
    zender_b.when_pressed = zender_b_rising 

    channel0.when_held = changePlaylist 
    channel0.when_released = changePlaylist 
    channel1.when_held = changePlaylist
    channel1.when_released = changePlaylist
    channel3.when_held = changePlaylist
    channel3.when_released = changePlaylist
    channel4.when_held = changePlaylist
    channel4.when_released = changePlaylist
    channel5.when_held = changePlaylist
    channel5.when_released = changePlaylist
    
    top1.when_pressed = setRepeatAndRandom 
    top1.when_released = setRepeatAndRandom 
    top2.when_pressed = setRepeatAndRandom
    top2.when_released = setRepeatAndRandom
    #top3.when_pressed = topButtons
    #top3.when_released = topButtons
    #top4.when_pressed = topButtons # enkel van belang voor playlists
    #top4.when_released = topButtons # enkel van belang voor playlists
    #top5.when_pressed = topButtons # enkel van belang voor playlists
    #top5.when_released = topButtons # enkel van belang voor playlists

    playing = None
    random = None 
    nextPrev = None 
    volumeChangeValue = None
    volume = 20

    ledTop(False, False, True) # blauw

    activePreset = None
    presets = ["Benedikt", "Janne", "Tijn", "sfeer", "List5", 
            "StuBru", "StuBruTijdloze", "Radio2", "Radio1", "Nostalgie", 
            "List11", "List12", "List13", "List14", "List15"]

    queue = {}
    msgId = 0; 
    timerOnOff = Timer(0.5, stoppedPlaying)
    timerZender = Timer(0.5, doChangeZender)
    timerVolume = Timer(0.5, doChangeVolume)
    timerPlaylist = Timer(0.5, changePlaylist)
    timerPing = Timer(1, ping)
    timerPing.start()

    while (True): 
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp("ws://localhost:6680/mopidy/ws/", on_message = on_message, on_open = on_open) 

        wst = Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()

        while (wst.isAlive()): 
            time.sleep(0.5)

        ledTop(True, False, False) # rood
        log ("websocket failed") 

        time.sleep(10) # bij websocket fail wordt om de 10 seconden opnieuw geprobeerd

