#!/usr/bin/python3
#####################
#                   #
#   IMPORTS         #
#                   #
##################### 
from __future__ import absolute_import, division, print_function, unicode_literals
import time
import os
import sys
import math
from tabulate import tabulate
import RPi.GPIO as GPIO
import threading
import random
from PIL import Image, ImageDraw, ImageFont
sys.path.append('..')
from lib import LCD_1inch28
from ADCPi import ADCPi

#####################
#                   #
#    SETUPS         #
#                   #
##################### 

# Setting up ADC board
try:
    adc = ADCPi(0x68, 0x69, 12)
except ImportError:
    print("Failed to import ADCPi from python system path")
    print("Importing from parent folder instead")
    try:
        import sys
        sys.path.append('..')
        from ADCPi import ADCPi
        adc = ADCPi(0x68, 0x69, 12)
    except ImportError:
        raise ImportError(
            "Failed to import library from parent folder")

# Setting up LCD
RST = 27
DC = 25
BL = 18
bus = 0
device = 0
disp = LCD_1inch28.LCD_1inch28()
rotation = 0

# Constants for 240x240 screen
WIDTH, HEIGHT = 240, 240
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2
RADIUS = 120  # Increased radius
ANGLE_START, ANGLE_END = 40, 320  # Angles for the 3/4 gauge arc (clockwise)

# Fonts
font = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 42)
font2 = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 20)
font3 = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 12)
gfont = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 54)

# Define the menus
topmenu = ["Gauges", "gaugemenu", "Config", "configmenu", "Multi 1", "QUAD_GAUGE", "backtotop1"]
gaugemenu = ["Boost", "BOOST", "Water °C", "COOLANT_TEMP", "Water Pres", "COOLANT_PRESSURE", "Fuel Pres", "FUEL_PRESSURE", "Oil Pres", "OIL_PRESSURE", "Oil °C", "OIL_TEMP", "Block °C", "BLOCK_TEMP", "Wideband", "WIDEBAND02", "Back", "backtotop1"]
configmenu = ["IP", "ipaddress", "Reboot", "reboot_pi", "Back", "backtotop3"]

# Define gauge items
gaugeItems = {
    "FUEL_PRESSURE": ["1", "Fuel Pres.", 1, 10, 15, 99, 110, 0, 150, "Kpa", 0],
    "BOOST": ["2", "Boost", 1, 0, -19, 24, 28, -20, 30, "psi", 0],
    "BLOCK_TEMP": ["3", "Engine °C", 1, 10, 15, 99, 110, 0, 150, "°C", 0],
    "COOLANT_PRESSURE": ["4", "H2O Pres.", 1, 10, 15, 99, 110, 0, 150, "Kpa", 0],
    "COOLANT_TEMP": ["5", "H2O °C", 1, 10, 15, 99, 110, 0, 150, "°C", 0],
    "OIL_PRESSURE": ["6", "Oil Pres.", 1, 10, 15, 99, 110, 0, 150, "Kpa", 0],
    "OIL_TEMP": ["7", "Oil °C", 1, 10, 15, 99, 110, 0, 150, "°C", 0],
    "WIDEBAND02": ["8", "O2 AFR", 1, 0.5, 1, 1.5, 2, 0, 4, "A/F", 0]
}

# Sensor constants
CONST_supply_voltage = 4.7

CONST_fuel_minVoltage = 0.48
CONST_fuel_maxVoltage = 4.5
CONST_fuel_minPressure = 0
CONST_fuel_maxPressure = 1000

CONST_coolant_minVoltage = 0.31
CONST_coolant_maxVoltage = 4.5
CONST_coolant_minPressure = 0
CONST_coolant_maxPressure = 1000

CONST_oil_minVoltage = 0.5
CONST_oil_maxVoltage = 4.5
CONST_oil_minPressure = 0
CONST_oil_maxPressure = 1000

CONST_boost_minVoltage = 0.4
CONST_boost_maxVoltage = 4.65
CONST_boost_minPressure = 20
CONST_boost_maxPressure = 300

CONST_blockTemp_balanceResistor = 1000.0
CONST_blockTemp_beta = 3600
CONST_blockTemproomTemp = 298.15
CONST_blockTempresistorRoomTemp = 3000

CONST_coolantTemp_balanceResistor = 1000.0
CONST_coolantTemp_beta = 3446
CONST_coolantTemproomTemp = 293.15
CONST_coolantTempresistorRoomTemp = 2480.0

CONST_oilTemp_balanceResistor = 1000.0
CONST_oilTemp_beta = 3446
CONST_oilTemproomTemp = 293.15
CONST_oilTempresistorRoomTemp = 2480.0

CONST_AFR_minVoltage = 0.68
CONST_AFT_maxVoltage = 1.36

#######################
#                     #
# Calculator functions#
#                     #
####################### 
def FUNCT_fuel_pres():
    voltage = adc.read_voltage(int(gaugeItems["FUEL_PRESSURE"][0]))
    gaugeItems["FUEL_PRESSURE"][2] = (voltage - CONST_fuel_minVoltage) / (CONST_fuel_maxVoltage - CONST_fuel_minVoltage) * (CONST_fuel_maxPressure - CONST_fuel_minPressure) + CONST_fuel_minPressure

def FUNCT_coolant_pres():
    cvoltage = adc.read_voltage(int(gaugeItems["COOLANT_PRESSURE"][0]))
    gaugeItems["COOLANT_PRESSURE"][2] = (cvoltage - CONST_coolant_minVoltage) / (CONST_coolant_maxVoltage - CONST_coolant_minVoltage) * (CONST_coolant_maxPressure - CONST_coolant_minPressure) + CONST_coolant_minPressure

def FUNCT_oil_pres():
    voltage = adc.read_voltage(int(gaugeItems["OIL_PRESSURE"][0]))
    gaugeItems["OIL_PRESSURE"][2] = (voltage - CONST_oil_minVoltage) / (CONST_oil_maxVoltage - CONST_oil_minVoltage) * (CONST_oil_maxPressure - CONST_oil_minPressure) + CONST_oil_minPressure

def FUNCT_boost_pres():
    voltage = adc.read_voltage(int(gaugeItems["BOOST"][0]))
    boostKpa = (voltage - CONST_boost_minVoltage) / (CONST_boost_maxVoltage - CONST_boost_minVoltage) * (CONST_boost_maxPressure - CONST_boost_minPressure) + CONST_boost_minPressure
    gaugeItems["BOOST"][2] = round(((boostKpa - 91.3) * 0.145038), 2)
    if gaugeItems["BOOST"][2] < 0:
        gaugeItems["BOOST"][9] = "inHg"
        gaugeItems["BOOST"][2] = round((abs(gaugeItems["BOOST"][2]) * 2.03602), 2)
    else:
        gaugeItems["BOOST"][9] = "psi"

def FUNCT_block_temp():
    voltage = adc.read_voltage(int(gaugeItems["BLOCK_TEMP"][0]))
    voltage = CONST_blockTemp_balanceResistor / voltage
    steinhart = voltage / CONST_blockTempresistorRoomTemp
    steinhart = math.log(steinhart)
    steinhart /= CONST_blockTemp_beta
    steinhart += 1.0 / (CONST_blockTemproomTemp)
    steinhart = 1.0 / steinhart
    steinhart -= 273.15
    gaugeItems["BLOCK_TEMP"][2] = round(steinhart, 2)

def FUNCT_coolant_temp():
    voltage = adc.read_voltage(int(gaugeItems["COOLANT_TEMP"][0]))
    resistance = CONST_coolantTemp_balanceResistor / (CONST_supply_voltage / voltage - 1)
    steinhart = resistance / CONST_coolantTempresistorRoomTemp
    steinhart = math.log(steinhart)
    steinhart /= CONST_coolantTemp_beta
    steinhart += 1.0 / (CONST_coolantTemproomTemp)
    steinhart = 1.0 / steinhart
    temperature = steinhart - 273.15  # Convert Kelvin to Celsius
    gaugeItems["COOLANT_TEMP"][2] = round(temperature, 2)

def FUNCT_oil_temp():
    voltage = adc.read_voltage(int(gaugeItems["OIL_TEMP"][0]))
    resistance = CONST_oilTemp_balanceResistor / (CONST_supply_voltage / voltage - 1)
    steinhart = resistance / CONST_oilTempresistorRoomTemp
    steinhart = math.log(steinhart)
    steinhart /= CONST_oilTemp_beta
    steinhart += 1.0 / (CONST_oilTemproomTemp)
    steinhart = 1.0 / steinhart
    temperature = steinhart - 273.15  # Convert Kelvin to Celsius
    gaugeItems["OIL_TEMP"][2] = round(temperature, 2)

def FUNCT_AFR():
    voltage = adc.read_voltage(int(gaugeItems["WIDEBAND02"][0]))
    AFR = (voltage - CONST_AFR_minVoltage) / (CONST_AFT_maxVoltage - CONST_AFR_minVoltage) * (4 - 0) + 0
    gaugeItems["WIDEBAND02"][2] = round(AFR, 2)

#####################
#                   #
#    MAIN LOOP      #
#                   #
##################### 
def main_loop():
    while True:
        # Update gauge values
        FUNCT_fuel_pres()
        FUNCT_coolant_pres()
        FUNCT_oil_pres()
        FUNCT_boost_pres()
        FUNCT_block_temp()
        FUNCT_coolant_temp()
        FUNCT_oil_temp()
        FUNCT_AFR()

        # Print gauges to LCD
        print_gauges()

        # Delay before next update
        time.sleep(1)

#####################
#                   #
#   PRINT GAUGES    #
#     FUNCTION      #
##################### 
def print_gauges():
    global topmenu
    while True:
        if topmenu[1]=="gaugemenu":
            for gauge in gaugemenu:
                # Draw gauge screen
                draw_gauge_screen(gauge)
                # Draw gauges
                draw_gauges(gauge)
                # Show image on LCD
                disp.display()

def draw_gauge_screen(gauge):
    global WIDTH, HEIGHT, CENTER_X, CENTER_Y, RADIUS, font, gfont, ANGLE_START, ANGLE_END
    image = Image.new("RGB", (WIDTH, HEIGHT), "BLACK")
    draw = ImageDraw.Draw(image)
    # Draw outer circle
    draw.ellipse([(CENTER_X - RADIUS, CENTER_Y - RADIUS), (CENTER_X + RADIUS, CENTER_Y + RADIUS)], outline="WHITE")
    # Draw arc
    start_angle = 90 - ANGLE_START
    end_angle = 90 - ANGLE_END
    draw.arc([(CENTER_X - RADIUS, CENTER_Y - RADIUS), (CENTER_X + RADIUS, CENTER_Y + RADIUS)], start_angle, end_angle, fill="WHITE", width=10)
    # Display gauge title
    title = gaugeItems[gauge][1]
    text_width, text_height = draw.textsize(title, font=gfont)
    draw.text((CENTER_X - text_width / 2, 10), title, font=gfont, fill="WHITE")
    disp.display(image)

def draw_gauges(gauge):
    global WIDTH, HEIGHT, CENTER_X, CENTER_Y, RADIUS, font, gfont, ANGLE_START, ANGLE_END
    image = Image.new("RGB", (WIDTH, HEIGHT), "BLACK")
    draw = ImageDraw.Draw(image)
    # Draw outer circle
    draw.ellipse([(CENTER_X - RADIUS, CENTER_Y - RADIUS), (CENTER_X + RADIUS, CENTER_Y + RADIUS)], outline="WHITE")
    # Draw arc
    start_angle = 90 - ANGLE_START
    end_angle = 90 - ANGLE_END
    draw.arc([(CENTER_X - RADIUS, CENTER_Y - RADIUS), (CENTER_X + RADIUS, CENTER_Y + RADIUS)], start_angle, end_angle, fill="WHITE", width=10)
    # Draw gauge value
    value = str(gaugeItems[gauge][2]) + " " + gaugeItems[gauge][9]
    text_width, text_height = draw.textsize(value, font=font)
    draw.text((CENTER_X - text_width / 2, CENTER_Y - text_height / 2), value, font=font, fill="WHITE")
    disp.display(image)

#####################
#                   #
#   MAIN FUNCTION   #
#                   #
##################### 
if __name__ == "__main__":
    main_loop()
