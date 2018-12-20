import websocket
import json
from threading import Timer, Thread
from gpiozero import Button, LED, OutputDevice
import datetime
import time
import subprocess

def on_message(ws, message): 
    global timerOnOff, queue, random
    event = json.loads(message) # decode received message
    try: 
        if "event" in event: # event thrown by mopidy
            if event['event'] == 'playback_state_changed':
                timerOnOff.cancel() 
                timerOnOff = Timer(0.5, stoppedPlaying)
                if event['new_state'] == 'playing': 
                    # if mopidy starts playing, immediately do things
                    startedPlaying() 
                elif event['new_state'] == 'stopped': 
                    # if mopidy stops playing, wait half a second to be sure it remains stopped before doing things
                    timerOnOff.start() 
            elif event['event'] == 'options_changed': 
                queue[sendCommand("core.tracklist.get_random", {})] = "random" # ask for random state
            else: 
                #print event
                pass
        elif "id" in event:  # response after request
            if event["id"] in queue: 
                if (queue[event["id"]] == "random"): # if I asked for random state
                    random = event["result"]
                    checkLEDs()
                queue.pop(event["id"], None) 
    except:
        log(event) 
        print("An exception occurred: %s" % event) 

def stoppedPlaying(): # is called by timerOnOff when mopidy stopped for 0.5s
    setPlaying(False) 

def startedPlaying(): # is called when mopidy says it's playing 
    setPlaying(True)

def setPlaying(value):
    global playing
    if (playing != value): # check if state is changed since last 'setPlaying' call
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
    shells(["mpc stop", "mpc clear", "mpc load %s" % playlist, "mpc play"])  # do commands, one after another

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

def changePlaylist(): # is called on hardware-button-press
    global timerPlaylist
    timerPlaylist.cancel() 
    timerPlaylist = Timer(0.5, checkPlaylist) # I use a timer to ensure stable state (my antique hardware buttons have a strange behaviour)
    timerPlaylist.start() 

def checkPlaylist(): # is called by timerPlaylist after 0.5s  
    if channel1.is_pressed: # button 1 is pressed: playlist 1
        startPlaylist("Benedikt") 
    elif channel3.is_pressed: # button 3 is pressed: playlist 3
        startPlaylist("Tijn")
    elif channel4.is_pressed: # button 4 is pressed: playlist 4
        startPlaylist("sfeer")
    elif channel5.is_pressed: # button 5 is pressed: playlist 5
        startPlaylist("radio")
    elif channel0.is_pressed: # button 0 is active: playlist 2 (button 2 could not be wired, but connection 0 is active as long as another button is pressed)
        startPlaylist("Janne")
    else: # no button is pressed
        stopPlayer()


def sendCommand(method, params):  # send websocket message
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

def shell(command): # run 1 command, don't wait
    proc = subprocess.Popen(command, shell=True)
    
def shells(commands): # run array of commands, wait for result
    for c in commands: 
        proc = subprocess.Popen(c, shell=True)
        if proc.wait() != 0:
            print("There was an error")
     
def on_open(ws): # on init 
    log ("websocket open")
    setRandom()
    setRepeat()
    setCrossfade() 

def log(line): 
    now = datetime.datetime.now()
    fullLine = "%d/%d %d:%d.%d - %s" % (now.day, now.month, now.hour, now.minute, now.second, line)
    shell("echo %s >> /root/siera/siera.log" % fullLine)
    print("%s" % fullLine)

def ping(): # just to check logs to see if it stays active
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
    
    top1 = Button(23, pull_up=True) # GPIO 23
    top2 = Button(22, pull_up=True) # GPIO 22
    top3 = Button(27, pull_up=True) # GPIO 27
    top4 = Button(17, pull_up=True) # GPIO 17 
    top5 = Button(24, pull_up=True) # GPIO 24   

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
