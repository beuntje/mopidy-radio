# mopidy-radio
Python script for controlling my Pi MusicBox and connected hardware

## Python dependencies: 
- websocket-client : https://github.com/websocket-client/websocket-client
- gpiozero

## hardware: 
- GPIO 14 - GND: button (switch channel)
- GPIO 15 - GND: button (switch channel)
- GPIO 4 - GND: button (switch channel)
- GPIO 2 - GND: button (switch channel)
- GPIO 3 - GND: button (switch channel)

- GPIO 23 - GND: button (repeat on/off)
- GPIO 22 - GND: button (repeat one on/off)
- GPIO 27 - GND: button (repeat on/of)
- GPIO 17 - GND: button ()
- GPIO 24 - GND: button ()

- GPIO 6 - GND - GPIO 12: Rotary encoder (volume down/up)
- GPIO 11 - GND - GPIO 8: Rotary encoder (previous / next)

- GPIO 10, GPIO 5, GPIO 9 - Resistor - GND: RGB LED 
- GPIO 25, GPIO 7, GPIO 18 - Resistor - GND: RGB LED 
- GPIO 20, GPIO 21, GPIO 26 - Resistor - GND: RGB LED 

- 5V - GND - GPIO 13: relais (to power external amplifier/speaker)


