# ===============================================================
#
# A simple game using
# - KY-023 XY Joystick Module
# - WS2812B programmable LED strip
#

# ===============================================================
#
# Register the joystick input
#

from machine import Pin, ADC
import machine
import time

import _thread

# Coordinates X and Y; must be on ADC capable pins
joystick_x = ADC(Pin(1))
joystick_y = ADC(Pin(2))
# Attenuation: ATTN_11DB is for [0-3.6V] scale.
# The 3.6V is maximum and the ADC pins can't read above that
joystick_x.atten(machine.ADC.ATTN_11DB)
joystick_y.atten(machine.ADC.ATTN_11DB)
# For pressing the joystick
joystick_sw = Pin(3,Pin.IN, Pin.PULL_UP)

# ===============================================================
#
# Initialize the LED strip
#

# Define a dictionary for color names and their RGB values
color = {
    "black": [0, 0, 0],
    "white": [255, 255, 255],
    "red": [255, 0, 0],
    "green": [0, 255, 0],
    "blue": [0, 0, 255],
    "yellow": [255, 255, 0],
    "magenta": [255, 0, 255]
}


LED_strip_data_pin = 0
LED_strip_length = 10

import neopixel
LED_strip = neopixel.NeoPixel(Pin(LED_strip_data_pin), LED_strip_length)

# Array to hold [r, g, b, brightness] for each LED
LED_strip_data_array = [color["yellow"] for _ in range(LED_strip_length)]

# Starting index
LED_strip_index = int(LED_strip_length / 2)

LED_strip_global_brightness = 0.05

# Handle moving the index selector left and right through the strip
def LED_strip_index_change(change):
    global LED_strip_length
    global LED_strip_index
    
    LED_strip_index += change
    if LED_strip_index < 0 :
        LED_strip_index = LED_strip_length-1
    elif LED_strip_index >= LED_strip_length :
        LED_strip_index = 0
    #print("\nDEBUG: INDEX", LED_strip_index)
    
    _thread.start_new_thread(breathing_led, (LED_strip_index,))

    
# Handle execution of the function on the currently selected index
def LED_strip_index_event():
    global LED_strip_index
    print("\nDEBUG:EVENT on index", LED_strip_index)
    #breathing_led(LED_strip_index)
    execute()

# ===============================================================
#
# Game victory check
#

from sys import exit

def game_victory_check():
    global LED_strip_length
    global LED_strip_data_array
    global color

    victory = True;
    for _ in range(LED_strip_length):
        if LED_strip_data_array[_] != color["black"] and LED_strip_data_array[_] != color["green"] :
            victory = False
            break
    if victory is not True: return
    else:
        exit()
        # TO-DO: reset brightness of the blinking light; stop mutex; blink with all; stop all user input

# ===============================================================
#
# Game functions
#

import random

def shuffle(lst):
    # Implement a basic shuffle by swapping elements in place
    for i in range(len(lst) - 1, 0, -1):
        j = random.randint(0, i)
        lst[i], lst[j] = lst[j], lst[i]

# Define example functions
def change_to_green(index, LED_strip_data_array):
    LED_strip_data_array[index] = color["green"]

def change_to_red(index, LED_strip_data_array):
    LED_strip_data_array[index] = color["red"]

def change_left_to_current_color(index, LED_strip_data_array):
    if index > 0:
        LED_strip_data_array[index - 1] = LED_strip_data_array[index]

def change_neighbors_to_blue(index, LED_strip_data_array):
    if index > 0:
        LED_strip_data_array[index - 1] = color["blue"]
    if index < LED_strip_length - 1:
        LED_strip_data_array[index + 1] = color["blue"]

# List of functions to be randomly assigned to colors
available_functions = [change_to_green, change_to_red, change_left_to_current_color, change_neighbors_to_blue]
shuffle(available_functions)

# Assign each color a random function from the shuffled list
function_library = {color_name: available_functions[i % len(available_functions)] for i, color_name in enumerate(color)}

# ===============================================================
#
# Game execute
#

def get_color_name(rgb_value):
    for name in color:
        if color[name] == rgb_value:
            return name
    return None

# Execute function based on current LED's color
def execute():
    global LED_strip_index
    global LED_strip_data_array
    global colors
    global function_library
    
    current_color = LED_strip_data_array[LED_strip_index]
    color_name = get_color_name(current_color)  # Use the helper function here
    print(color_name)
    if color_name and color_name in function_library:
        function_library[color_name](LED_strip_index, LED_strip_data_array)
    LED_strip_index_change(0)
    game_victory_check()

# ===============================================================
#
# Actual functions of the LED strip
#

breathing_led_mutex = False

def breathing_led(index):
    global LED_strip_data_array
    global LED_strip_global_brightness
    global LED_strip
    global LED_strip_length
    
    global breathing_led_mutex
    
    # Stop the previous thread
    breathing_led_mutex = False
    time.sleep(0.05)
    brightness = LED_strip_global_brightness
    for _ in range(LED_strip_length):
        r, g, b = LED_strip_data_array[_]
        LED_strip[_] = (int(r * brightness), int(g * brightness), int(b * brightness))
        LED_strip.write()

    # Start new thread
    r, g, b = LED_strip_data_array[index]
    direction = 1
    step = 0.004
    breathing_led_mutex = True
    #print("DEBUG: starting thread")

    while breathing_led_mutex:
        if brightness >= 0.3 - step:
            direction = -1
        elif brightness <= 0.1 + step:
            direction = 1

        brightness += direction * step
        LED_strip[index] = (int(r * brightness), int(g * brightness), int(b * brightness))
        LED_strip.write()
        time.sleep(0.01)

    #print("DEBUG: finishing thread")
    


# ===============================================================
#
# Loop for handling the user input
#

def get_user_input():
    # Support variables
    last_x = 0
    last_y = 0
    last_sw = 1

    while True:
        time.sleep(0.1)
        joystick_x_value, joystick_y_value, joystick_sw_value = joystick_x.read(), joystick_y.read(), joystick_sw.value()
        #print(joystick_x_value, joystick_y_value, joystick_sw_value)

        # Moving left or right
        if 1000 < joystick_y_value < 3000:
            last_y = 0
        elif joystick_y_value < 1000 and last_y != -1:
            last_y = -1
            LED_strip_index_change(-1)
        elif joystick_y_value > 3000 and last_y != 1:
            last_y = 1
            LED_strip_index_change(1)
            
        # Moving up or down
        if 100 < joystick_x_value < 4000:
            last_x = 0
        elif joystick_x_value < 100 and last_x != -1:
            last_x = -1
            LED_strip_index_event()
        elif joystick_x_value > 4000 and last_x != 1:
            last_x = 1
            LED_strip_index_event()

        # Pressing the jostick
        if joystick_sw_value == 1 and last_sw == 0:
            last_sw = 1
        elif joystick_sw_value == 0 and last_sw != 0:
            last_sw = 0
            LED_strip_index_event()

# ===============================================================

#_thread.start_new_thread(get_user_input, ())
LED_strip_index_change(0)
get_user_input()




