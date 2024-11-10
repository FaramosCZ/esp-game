from machine import Pin, ADC
import machine
import time
import _thread
import random
import neopixel
from sys import exit

# ===============================================================
#
# Constants
#

COLOR_MAP = {
    "black":   [0,   0,   0  ],
    "white":   [255, 255, 255],
    "red":     [255, 0,   0  ],
    "green":   [0,   255, 0  ],
    "blue":    [0,   0,   255],
    "yellow":  [255, 255, 0  ],
    "magenta": [255, 0,   255]
}

# ===============================================================
#
# KY-023 XY Joystick Module
#

class Joystick:
    def __init__(self, x_pin, y_pin, sw_pin):
        self.x = ADC(Pin(x_pin))
        self.y = ADC(Pin(y_pin))
        # Attenuation: ATTN_11DB is for [0-3.6V] scale.
        # The 3.6V is maximum and the ADC pins can't read above that
        self.x.atten(ADC.ATTN_11DB)
        self.y.atten(ADC.ATTN_11DB)

        # For pressing the joystick
        self.sw = Pin(sw_pin, Pin.IN, Pin.PULL_UP)

        self.last_x = 4096/2
        self.last_y = 4096/2
        self.last_sw = 1

    def read(self):
        return self.x.read(), self.y.read(), self.sw.value()
    
    def update(self):
        x, y, sw = self.read()

        # TO-DO: here I can optionally block pressing X and Y at the same time

        if 100 < x < 4000:
            result_x = self.last_x = 0        
        elif x < 100 and self.last_x != -1:
            result_x = self.last_x = -1
        elif x > 4000 and self.last_x != 1:
            result_x = self.last_x = 1
        else:
            result_x = 0

        if 1000 < y < 3000:
            result_y = self.last_y = 0        
        elif y < 1000 and self.last_y != -1:
            result_y = self.last_y = -1
        elif y > 3000 and self.last_y != 1:
            result_y = self.last_y = 1
        else:
            result_y = 0

        if sw == 0 and self.last_sw != 0:
            self.last_sw = 0
            result_sw = 0
        else:
            self.last_sw = 1
            result_sw = 1

        return result_x, result_y, result_sw

# ===============================================================
#
# WS2812B programmable LED strip
#

class LEDStrip:
    def __init__(self, pin, length):
        self.strip = neopixel.NeoPixel(Pin(pin), length)
        self.data = [COLOR_MAP["green"] for _ in range(length)]
        self.index = length // 2
        self.brightness = 0.05
        self.length = length
        self.pin = pin
        
        self.update()
        
    def index_change(self, value):
        self.index += value
        if self.index < 0 :
            self.index = self.length-1
        elif self.index >= self.length :
            self.index = 0

    def set_color(self, index, color):
        self.data[index] = color
        self.update()

    def get_color(self, index):
        current_color = tuple(self.data[index])
        color_name = None
        for name, rgb in COLOR_MAP.items():
            if tuple(rgb) == current_color:
                color_name = name
                break
        if not color_name:
            print("Unexpected error: color not identified")
        return color_name

    def update(self):
        for i in range(self.length):
            r, g, b = self.data[i]
            self.strip[i] = (int(r * self.brightness), int(g * self.brightness), int(b * self.brightness))
        self.strip.write()

    def breathe(self):
        # THREAD: breathing light on LED strip index currently selected by the user
        _thread.start_new_thread(self._breathing_effect, ())

    def _breathing_effect(self):
        while True:
            index = self.index
            r, g, b = self.data[index]
            brightness = self.brightness
            direction = 1
            step = 0.004

            while True:
                if index != self.index:
                    self.strip[index] = (int(r * self.brightness), int(g * self.brightness), int(b * self.brightness))
                    self.strip.write()
                    break

                if brightness >= 0.3 - step:
                    direction = -1
                elif brightness <= 0.1 + step:
                    direction = 1
                brightness += direction * step
                self.strip[index] = (int(r * brightness), int(g * brightness), int(b * brightness))
                self.strip.write()
                time.sleep(0.01)

# ===============================================================
#
# LEDGameFunctions
#

class LEDGameFunctions:
    def __init__(self, led_strip):
        self.led_strip = led_strip
        
    def execute():
        self.execute_function()
        pass

    def _shuffle(self, lst):
        # Implement a basic shuffle by swapping elements in place
        for i in range(len(lst) - 1, 0, -1):
            j = random.randint(0, i)
            lst[i], lst[j] = lst[j], lst[i]
        
    def assign_function(self, to_color):
        functions = [
            self.change_to_color
        ]
        self._shuffle(functions)

        self.execute_function = functions[0]
    
    def change_to_color():
        pass
    
    def change_to_green(self, index):
        self.led_strip.set_color(index, COLOR_MAP["green"])

    def change_to_red(self, index):
        self.led_strip.set_color(index, COLOR_MAP["red"])

    def change_left_to_current_color(self, index):
        if index > 0:
            self.led_strip.set_color(index - 1, self.led_strip.data[index])

    def change_neighbors_to_blue(self, index):
        if index > 0:
            self.led_strip.set_color(index - 1, COLOR_MAP["blue"])
        if index < self.led_strip.length - 1:
            self.led_strip.set_color(index + 1, COLOR_MAP["blue"])

# ===============================================================
#
# Game
#

class Game:
    def __init__(self, joystick, led_strip, difficulty):
        self.joystick = joystick
        self.led_strip = led_strip
        self.difficulty = difficulty
        
        self.game_setup()

    def game_setup(self):
        self.color_functions = {}
        pass

    def execute(self):
        self.color_functions[self.led_strip.get_color(self.led_strip.index)].execute()
        self.check_victory()

    def check_victory(self):
        if all(color in [COLOR_MAP["green"], COLOR_MAP["black"]] for color in self.led_strip.data):
            print("Victory!")
            exit()
            # TO-DO: while True to for infinity once the game is finished ?
            #   note: that won't stop the threaded tasks though

    def user_input_handler(self):
        self.led_strip.breathe()

        while True:
            time.sleep(0.1)
            x, y, sw = self.joystick.update()

            self.led_strip.index_change(y)
            
            if x != 0:
                self.execute()

            if sw != 1:
                self.execute()

# ===============================================================
#
# Initialize and start the game
#

joystick = Joystick(x_pin=1, y_pin=2, sw_pin=3)
led_strip = LEDStrip(pin=0, length=10)

game = Game(joystick, led_strip, difficulty=5)

game.user_input_handler()

