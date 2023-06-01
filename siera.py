import math
import RPi.GPIO as GPIO
from event import Event
from threading import Timer
from log import Log
from config import Config


class Siera(object):
  __timers = {}
  __log = Log()
  __active = False
  __current_preset = False

  def __init__(self):
    self.__event = Event()

    config = Config()

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    self.__buttons_preset_configure([
      int(config.value['Preset']['a']),
      int(config.value['Preset']['b']),
      int(config.value['Preset']['c']),
      int(config.value['Preset']['d']),
      int(config.value['Preset']['e'])
    ])
    self.__current_preset = self.selected_preset()

    self.__buttons_options_configure([
      int(config.value['TopButton']['a']),
      int(config.value['TopButton']['b']),
      int(config.value['TopButton']['c']),
      int(config.value['TopButton']['d']),
      int(config.value['TopButton']['e'])
    ])

    self.__rotary_volume_configure([
      int(config.value['Volume']['up']),
      int(config.value['Volume']['down'])
    ])

    self.__rotary_channel_configure([
      int(config.value['Channel']['up']),
      int(config.value['Channel']['down'])
    ])

    self.__power_led_configure([
      int(config.value['TopLED']['red']),
      int(config.value['TopLED']['green']),
      int(config.value['TopLED']['blue'])
    ])

    self.__background_led_configure([
      int(config.value['LeftLED']['red']),
      int(config.value['LeftLED']['green']),
      int(config.value['LeftLED']['blue']),
      int(config.value['RightLED']['red']),
      int(config.value['RightLED']['green']),
      int(config.value['RightLED']['blue'])
    ])

    self.__relais_configure(int(config.value['Output']['relais']))

    self.__active = True

    def reset_reset():
      self.__reset_counters = {}
      if "check_reset" in self.__timers: del self.__timers["check_reset"]

    def check_reset(btn, value):
      if not btn in self.__reset_counters:
        self.__reset_counters[btn] = 0
      else:
        self.__reset_counters[btn] += 1

      if self.__reset_counters[btn] > 1:
        self.__log.add("reset counter {}: {}".format(btn, self.__reset_counters[btn]), "siera")
      if self.__reset_counters[btn] == 5:
        self.__event.execute("siera.reset.{}".format(btn))

      if not "check_reset" in self.__timers:
        self.__timers["check_reset"] = Timer(5, reset_reset)
        self.__timers["check_reset"].start()

    self.on_option_change(check_reset)
    self.__reset_counters = {}


  # ---------- Rotary encoder volume ----------

  def __rotary_volume_configure(self, pins):
    self.__rotary_volume = []
    self.__rotary_volume_change = 0
    for pin in pins:
      GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
      GPIO.add_event_detect(pin, GPIO.RISING, callback=self.__rotary_volume_turn)
      self.__rotary_volume.append(pin)

  def __rotary_volume_turn(self, pin):
    def rotary_volume_turn_send():
      value =  self.__rotary_volume_change / 5
      if (value == 0 and self.__rotary_volume_change != 0):
        if self.__rotary_volume_change>0:
          value = 1
        else:
          value = -1
      if self.__active:
        self.__event.execute("siera.volumeturn", value )
        self.__log.add("volume turn:  {}".format(value), "siera")
      self.__rotary_volume_change = 0
      del self.__timers["rotary_volume"]

    if (GPIO.input(self.__rotary_volume[0]) != GPIO.input(self.__rotary_volume[1])):
      if self.__rotary_volume[0]==pin:
        self.__rotary_volume_change += 1
      else:
        self.__rotary_volume_change -= 1

    if not "rotary_volume" in self.__timers:
      self.__timers["rotary_volume"] = Timer(0.2, rotary_volume_turn_send)
      self.__timers["rotary_volume"].start()


  def on_volume_turn(self, callback):
    self.__event.register("siera.volumeturn", callback)

  # ---------- Rotary encoder channel ----------

  def __rotary_channel_configure(self, pins):
    self.__rotary_channel = []
    self.__rotary_channel_change = 0
    for pin in pins:
      GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
      GPIO.add_event_detect(pin, GPIO.RISING, callback=self.__rotary_channel_turn)
      self.__rotary_channel.append(pin)

  def __rotary_channel_turn(self, pin):
    def rotary_channel_turn_send():
      value = (1 if self.__rotary_channel_change>0 else -1)
      if self.__active:
        self.__event.execute("siera.channelturn", value )
        self.__log.add("channel turn:  {}".format(value), "siera")
      self.__rotary_channel_change = 0
      del self.__timers["rotary_channel"]

    if (GPIO.input(self.__rotary_channel[0]) == GPIO.input(self.__rotary_channel[1])):
      #if self.__rotary_channel[0]==pin:
      #  self.__rotary_channel_change -= 1
      #else:
      #  self.__rotary_channel_change += 1
      pass
    else:
      if self.__rotary_channel[0]==pin:
        self.__rotary_channel_change += 1
      else:
        self.__rotary_channel_change -= 1

    if not "rotary_channel" in self.__timers:
      self.__timers["rotary_channel"] = Timer(0.9, rotary_channel_turn_send)
      self.__timers["rotary_channel"].start()


  def on_channel_turn(self, callback):
    self.__event.register("siera.channelturn", callback)

  # ---------- Preset buttons ----------

  def __buttons_preset_configure(self, pins):
    self.__buttons_presets = []
    for pin in pins:
      GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
      GPIO.add_event_detect(pin, GPIO.RISING, callback=self.__button_preset_pressed)
      self.__buttons_presets.append(pin)

  def __button_preset_pressed(self, pin):
    def wait_until_stable():
      preset = self.selected_preset()

      if self.__current_preset == preset:
        return

      self.__current_preset = preset
      self.__log.add("preset {} pressed".format(preset), "siera")
      if (preset > 0):
        if self.__active: self.__event.execute("siera.presetbutton", preset)
      else:
        if self.__active: self.__event.execute("siera.stop")
      if "preset_change" in self.__timers: del self.__timers["preset_change"]

    if "preset_change" in self.__timers:
      self.__timers["preset_change"].cancel()
    self.__timers["preset_change"] = Timer(0.5, wait_until_stable)
    self.__timers["preset_change"].start()

  def on_stop(self, callback):
    self.__event.register("siera.stop", callback)

  def on_preset_change(self, callback):
    self.__event.register("siera.presetbutton", callback)


  def selected_preset(self):
    if not GPIO.input(self.__buttons_presets[1]):
        preset = 1
    elif not GPIO.input(self.__buttons_presets[2]):
        preset = 3
    elif not GPIO.input(self.__buttons_presets[3]):
        preset = 4
    elif not GPIO.input(self.__buttons_presets[4]):
        preset = 5
    elif not GPIO.input(self.__buttons_presets[0]):
        preset = 2
    else:
        preset = 0
    return preset


  def preset_is_selected(self, nr):
    return self.selected_preset() == nr

  # ---------- Option buttons ----------

  def __buttons_options_configure(self, pins):
    self.__buttons_options = []
    for pin in pins:
      GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
      GPIO.add_event_detect(pin, GPIO.RISING, callback=self.__button_options_pressed)
      self.__buttons_options.append(pin)

  def __button_options_pressed(self, event_pin):
    def wait_until_stable():
      nr = 0
      for option_pin in self.__buttons_options:
        if event_pin == option_pin and self.__active: self.__event.execute("siera.optionbutton", nr, self.option_is_down(nr))
        nr += 1

    if "option_change_{}".format(event_pin) in self.__timers:
      self.__timers["option_change_{}".format(event_pin)].cancel()
    self.__timers["option_change_{}".format(event_pin)] = Timer(0.25, wait_until_stable)
    self.__timers["option_change_{}".format(event_pin)].start()


  def on_option_change(self, callback):
    self.__event.register("siera.optionbutton", callback)

  def option_is_down(self, nr):
    if nr in [1]:
      return GPIO.input(self.__buttons_options[nr])
    else:
      return not GPIO.input(self.__buttons_options[nr])


  # ---------- Relais ----------

  def __relais_configure(self, pin):
    GPIO.setup(pin, GPIO.OUT)
    self.__relais = pin


  def relais(self, power):
    GPIO.output(self.__relais, power)

  # ---------- Top LED (power) ----------

  def __power_led_configure(self, pins):
    self.__power_led = []
    for pin in pins:
      GPIO.setup(pin, GPIO.OUT)
      led = GPIO.PWM(pin, 100) # PWM Frequency: 100
      led.start(0)
      self.__power_led.append(led)


  def power_led(self, color_values):
    i=0
    for led in self.__power_led:
      led.ChangeDutyCycle(color_values[i])
      i += 1

  def power_led_rainbow(self, sec = 5):
    def power_led_rainbow_interval():
      frequency = .3
      remaining_calls = calls - 1

      self.__power_led[0].ChangeDutyCycle(math.sin(frequency*remaining_calls + 0) * 50 + 50)
      self.__power_led[1].ChangeDutyCycle(math.sin(frequency*remaining_calls + 2) * 50 + 50)
      self.__power_led[2].ChangeDutyCycle(math.sin(frequency*remaining_calls + 4) * 50 + 50)

      if (remaining_calls > 0):
        self.power_led_rainbow(remaining_calls)
      else:
        del self.__timers["power_led_rainbow"]

    speed = 0.03
    calls = sec
    if not "power_led_rainbow" in self.__timers:
      calls = sec / speed
    self.__timers["power_led_rainbow"] = Timer(speed, power_led_rainbow_interval)
    self.__timers["power_led_rainbow"].start()

  # ---------- Bottom LEDs (background) ----------

  def __background_led_configure(self, pins):
    self.__background_led = []
    for pin in pins:
      GPIO.setup(pin, GPIO.OUT)
      led =  GPIO.PWM(pin, 100) # PWM Frequency: 100
      led.start(0)
      self.__background_led.append(led)

  def background_led(self, color_values):
    i=0
    for led in self.__background_led:
      led.ChangeDutyCycle(color_values[i])
      i += 1

  # ---------- Emergency button ----------

  def on_option_5clicks(self, nr, callback):
    self.__event.register("siera.reset.{}".format(nr), callback)

  # ---------- Default ----------

  def cleanup(self):
    GPIO.cleanup()
