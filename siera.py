import websocket
import json
from threading import Timer, Thread
from gpiozero import Button, LED, OutputDevice
import datetime
import time
import subprocess

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
                    checkLEDs()
                queue.pop(event["id"], None)
    except:
        log(event) 
        print("An exception occurred: %s" % event) 

def stoppedPlaying():
    setPlaying(False)

def startedPlaying():
    setPlaying(True)

def setPlaying(value):
    global playing
    if (playing != value): 
        playing = value 
        checkLEDs()
        if (playing): 
            log ("started playing")
            relais.on()
        else: 
            log ("stopped playing")
            relais.off()

def startPlaylist(playlist): 
    log ("load playlist %s" % playlist)
    shells(["mpc stop", "mpc clear", "mpc load %s" % playlist, "mpc play"])

def stopPlayer(): 
    shell("mpc stop")

def volume_a_rising():
    if volume_b.is_pressed: 
        shell("mpc volume +2")

def volume_b_rising():
    if volume_a.is_pressed:  
        shell("mpc volume -2")

def zender_a_rising(): 
    if zender_b.is_pressed:
        shell("mpc next")

def zender_b_rising():
    if zender_a.is_pressed:
        shell("mpc previous")

def checkLEDs(): 
    global playing, random
    if (playing): 
        ledBottom.on() 
        if random: 
            ledTop.on()
        else: 
            ledTop.off()
    else: 
        ledBottom.off()
        ledTop.off()

def changePlaylist(): 
    global timerPlaylist
    timerPlaylist.cancel() 
    timerPlaylist = Timer(0.5, checkPlaylist)
    timerPlaylist.start() 

def checkPlaylist():
    if channel1.is_pressed: # knop 1
        startPlaylist("Benedikt") 
    elif channel3.is_pressed: # knop 3
        startPlaylist("Tijn")
    elif channel4.is_pressed: # knop 4
        startPlaylist("sfeer")
    elif channel5.is_pressed: # knop 5
        startPlaylist("radio")
    elif channel0.is_pressed: # knop 2
        startPlaylist("Janne")
    else:
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

def setRandom(): 
    if top3.is_pressed: 
        shell("mpc random off")
    else: 
        shell("mpc random on") 

def setRepeat(): 
    if top1.is_pressed: 
        shell("mpc single on") 
        shell("mpc repeat off") 
    elif top2.is_pressed: 
        shell("mpc single on") 
        shell("mpc repeat on") 
    else: 
        shell("mpc single off") 
        shell("mpc repeat off") 

def setCrossfade():  
    if top4.is_pressed: 
        #shell("mpc crossfade 1") 
        pass
    elif top5.is_pressed: 
        #shell("mpc crossfade 3") 
        pass
    else: 
        #shell("mpc crossfade 0") 
        pass

def shell(command): 
    proc = subprocess.Popen(command, shell=True)
    
def shells(commands): 
    for c in commands: 
        proc = subprocess.Popen(c, shell=True)
        if proc.wait() != 0:
            print("There was an error")
     
def on_open(ws):
    log ("websocket open")
    setRandom()
    setRepeat()
    setCrossfade() 

def log(line): 
    now = datetime.datetime.now()
    fullLine = "%d/%d %d:%d.%d - %s" % (now.day, now.month, now.hour, now.minute, now.second, line)
    shell("echo %s >> /root/siera/siera.log" % fullLine)
    print("%s" % fullLine)

def ping(): 
    global timerPing
    log("ping")
    timerPing.cancel()
    timerPing = Timer(60 * 15, ping) # 15 minuten
    timerPing.start()

if __name__ == "__main__":
    print "start script"
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
    
    top1 = Button(23, pull_up=True) # GPIO
    top2 = Button(22, pull_up=True) # GPIO
    top3 = Button(27, pull_up=True) # GPIO
    top4 = Button(17, pull_up=True) # GPIO
    top5 = Button(24, pull_up=True) # GPIO

    ledTop = LED(10) #GPIO 10
    ledBottom = LED(21) #GPIO 21

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
    
    top1.when_pressed = setRepeat 
    top1.when_released = setRepeat 
    top2.when_pressed = setRepeat
    top2.when_released = setRepeat
    top3.when_pressed = setRandom
    top3.when_released = setRandom
    top4.when_pressed = setCrossfade
    top4.when_released = setCrossfade
    top5.when_pressed = setCrossfade
    top5.when_released = setCrossfade

    playing = None
    random = None 
    queue = {}
    msgId = 0; 
    timerOnOff = Timer(0.5, stoppedPlaying)
    timerPlaylist = Timer(0.5, changePlaylist)
    timerPing = Timer(1, ping)
    timerPing.start()
 
    while (True): 
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp("ws://localhost:6680/mopidy/ws/", on_message = on_message, on_open = on_open) 
        ws.run_forever()
        log ("websocket failed") 
        time.sleep(10)

    log ("stopped script")
