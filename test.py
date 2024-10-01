from __future__ import absolute_import, division, print_function, unicode_literals
from PIL import Image, ImageDraw, ImageFont
import time
import threading
import RPi.GPIO as GPIO
import time
import os
import sys
import math
from tabulate import tabulate
sys.path.append('..')
import signal
import random
import socket
from lib import LCD_1inch28

try:
    from ADCPi import ADCPi
except ImportError:
    print("Failed to import ADCPi from python system path")
    print("Importing from parent folder instead")
    try:
        import sys
        sys.path.append('..')
        from ADCPi import ADCPi
    except ImportError:
        raise ImportError(
            "Failed to import library from parent folder")

adc = ADCPi(0x68, 0x69, 12)



########################
#                      #
#   MENU  Variable     #
#                      #
########################


# Define the menus
level1_menu = ["Gauges", "MultiGauge", "Config"]
multigauge_menu = ["QuadTemp", "Triple Stack", "Back"]
config_menu = ["ip address", "reboot pi", "Back"]


current_menu = "level1"
menu_indices = {
    "level1": 0,
    "multigauge": 0,
    "config": 0,
    "gauges": 0
}


########################
#                      #
#   Screen Variables   #
#                      #
########################
RST = 27
DC = 25
BL = 18
bus = 0
device = 0
disp = LCD_1inch28.LCD_1inch28()
rotation = 0
disp.Init()


# Constants for 240x240 screen
WIDTH, HEIGHT = 240, 240
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2
RADIUS = 120  # Increased radius
ANGLE_START, ANGLE_END = 40, 320  # Angles for the 3/4 gauge arc (clockwise)


# Define colors
BACKGROUND_COLOR = (30, 30, 30)
TEXT_COLOR_SELECTED = (255, 0, 0)
TEXT_COLOR_NON_SELECTED1 = (255, 255, 255)  # White
TEXT_COLOR_NON_SELECTED2 = (0, 0, 255)      # Blue
FONT_SIZE = 30

# Define fonts
font = ImageFont.truetype("arial.ttf", FONT_SIZE)
font1 = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 42)
font2 = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 20)
font3 = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 12)
gfont = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 54)

smallfont = ImageFont.truetype("arial.ttf", FONT_SIZE - 10)
large_font = ImageFont.truetype("arial.ttf", FONT_SIZE + 14)

# Setup GPIO for buttons
SCROLL_PIN = 38
SELECT_PIN = 40
GPIO.setmode(GPIO.BOARD)
GPIO.setup(SCROLL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SELECT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)



########################
#                      #
#   Gauge  Variables   #
#                      #
########################


# Define gauge items
gaugeItems = {
    "FUEL_PRESSURE": ["1", "Fuel Pres.", 1, 10, 15, 99, 110, 0, 150, "Kpa", 0],
    "BOOST": ["2", "Boost", 1, 0, -19, 24, 28, -20, 30, "psi", 0],
    "BLOCK_TEMP": ["3", "Engine °C", 1, 10, 15, 99, 110, 0, 150, "°C", 0],
    "COOLANT_PRESSURE": ["4", "H2O Pres.", 1, 10, 15, 99, 110, 0, 150, "Kpa", 0],
    "COOLANT_TEMP": ["5", "H2O °C", 1, 10, 15, 99, 110, 0, 150, "°C", 0],
    "OIL_PRESSURE": ["6", "Oil Pres.", 1, 10, 15, 99, 110, 0, 150, "Kpa", 0],
    "OIL_TEMP": ["7", "Oil °C", 1, 10, 15, 99, 110, 0, 150, "°C", 0],
    "WIDEBAND02": ["8", "O2 AFR", 1, .5, 1, 1.5, 2, 0, 4, "A/F", 0]
}

gauge_keys = list(gaugeItems.keys())
gauge_menu = [gaugeItems[key][1] for key in gauge_keys] + ["Back"]




#####################
#                   #
#SENSOR CONSTANT    #
#                   #
##################### 
CONST_supply_voltage =4.5

CONST_fuel_minVoltage =.5
CONST_fuel_maxVoltage =4.5
CONST_fuel_minPressure =0
CONST_fuel_maxPressure =1000

CONST_coolant_minVoltage =.31
CONST_coolant_maxVoltage =5
CONST_coolant_minPressure =0
CONST_coolant_maxPressure =1000

CONST_oil_minVoltage =.35
CONST_oil_maxVoltage =4.5
CONST_oil_minPressure =0
CONST_oil_maxPressure =1000

CONST_boost_minVoltage =.4
CONST_boost_maxVoltage =4.5
CONST_boost_minPressure =20
CONST_boost_maxPressure =300

#CONST_blockTemp_balanceResistor = 1000.0
#CONST_blockTemp_beta = 3600
#CONST_blockTemproomTemp = 298.15 
#CONST_blockTempresistorRoomTemp =3000 

CONST_blockTemp_balanceResistor = 1000.0
CONST_blockTemp_beta = 3600
CONST_blockTemproomTemp = 298.15 
CONST_blockTempresistorRoomTemp =2480 

CONST_coolantTemp_balanceResistor = 1000.0
CONST_coolantTemp_beta = 3446
CONST_coolantTemproomTemp = 293.15
CONST_coolantTempresistorRoomTemp = 2480.0

CONST_oilTemp_balanceResistor = 1000.0
CONST_oilTemp_beta = 3446
CONST_oilTemproomTemp = 293.15
CONST_oilTempresistorRoomTemp = 2480.0

CONST_AFR_minVoltage=0
CONST_AFT_maxVoltage=5
CONST_AFR_minlamba=.68
CONST_AFT_malamba=1.36



#######################
#                     #
#Calculator functions #
#                     #
####################### 
def FUNCT_fuel_pres():
    try:
        voltage=adc.read_voltage(int(gaugeItems["FUEL_PRESSURE"][0]))
        gaugeItems["FUEL_PRESSURE"][2]= (voltage - CONST_fuel_minVoltage)/(CONST_fuel_maxVoltage -CONST_fuel_minVoltage)*(CONST_fuel_maxPressure- CONST_fuel_minPressure) + CONST_fuel_minPressure
    except:
        gaugeItems["FUEL_PRESSURE"][2]=round(1,2)

def FUNCT_coolant_pres():
    try:
        cvoltage=adc.read_voltage(int(gaugeItems["COOLANT_PRESSURE"][0]))
        gaugeItems["COOLANT_PRESSURE"][2]= (cvoltage - CONST_coolant_minVoltage)/(CONST_coolant_maxVoltage - CONST_coolant_minVoltage)*(CONST_coolant_maxPressure- CONST_coolant_minPressure) + CONST_coolant_minPressure
    except:
        gaugeItems["COOLANT_PRESSURE"][2]=round(1,2)



def FUNCT_AFR():
    try:
        cvoltage=adc.read_voltage(int(gaugeItems["WIDEBAND02"][0]))
        gaugeItems["WIDEBAND02"][2]= (cvoltage - CONST_AFR_minVoltage)/(CONST_AFT_maxVoltage - CONST_AFR_minVoltage)*(CONST_AFT_malamba- CONST_AFR_minlamba) + CONST_AFR_minlamba
    except:
        gaugeItems["WIDEBAND02"][2]=round(1,2)

def FUNCT_oil_pres():
    try:
        voltage=adc.read_voltage(int(gaugeItems["OIL_PRESSURE"][0]))
        gaugeItems["OIL_PRESSURE"][2]= (voltage - CONST_oil_minVoltage)/(CONST_oil_maxVoltage -CONST_oil_minVoltage)*(CONST_oil_maxPressure- CONST_oil_minPressure) + CONST_oil_minPressure
    except:
        gaugeItems["OIL_PRESSURE"][2]=round(1,2)

def FUNCT_boost_pres():
    try:
        voltage=adc.read_voltage(int(gaugeItems["BOOST"][0]))
        boostKpa= (voltage - CONST_boost_minVoltage)/(CONST_boost_maxVoltage -CONST_boost_minVoltage)*(CONST_boost_maxPressure- CONST_boost_minPressure) + CONST_boost_minPressure
        gaugeItems["BOOST"][2]=round(((boostKpa-91.3)*0.145038),2)
#        if gaugeItems["BOOST"][2] < 0:
##            gaugeItems["BOOST"][9] = "inHg"
 #           gaugeItems["BOOST"][2]=round((abs(gaugeItems["BOOST"][2])*2.03602),2)
#        else:
#            gaugeItems["BOOST"][9] = "psi"
    except:
        gaugeItems["BOOST"][2]=round(1,2)

def FUNCT_block_temp():
    try:
        voltage=adc.read_voltage(int(gaugeItems["BLOCK_TEMP"][0]))
        voltage=CONST_blockTemp_balanceResistor/voltage
        steinhart = voltage /CONST_blockTempresistorRoomTemp 
        steinhart = math.log(steinhart) 
        steinhart /=CONST_blockTemp_beta
        steinhart += 1.0 / (CONST_blockTemproomTemp)
        steinhart = 1.0 / steinhart
        steinhart -= 273.15
        gaugeItems["BLOCK_TEMP"][2]=round(steinhart,2)
    except:
        gaugeItems["BLOCK_TEMP"][2]=round(1,2)

def FUNCT_coolant_temp():
    try:
        voltage=adc.read_voltage(int(gaugeItems["COOLANT_TEMP"][0]))
        resistance = CONST_coolantTemp_balanceResistor / (CONST_supply_voltage / voltage - 1)
        steinhart = resistance / CONST_coolantTempresistorRoomTemp
        steinhart = math.log(steinhart)
        steinhart /= CONST_coolantTemp_beta
        steinhart += 1.0 / (CONST_coolantTemproomTemp)
        steinhart = 1.0 / steinhart
        temperature = steinhart - 273.15  # Convert Kelvin to Celsius
        gaugeItems["COOLANT_TEMP"][2]=round(temperature,2)
    except:
        gaugeItems["COOLANT_TEMP"][2]=round(1,2)

def FUNCT_oil_temp():
    try :
        voltage=adc.read_voltage(int(gaugeItems["OIL_TEMP"][0]))
        resistance = CONST_oilTemp_balanceResistor / (CONST_supply_voltage / voltage - 1)
        steinhart = resistance / CONST_oilTempresistorRoomTemp
        steinhart = math.log(steinhart)
        steinhart /= CONST_oilTemp_beta
        steinhart += 1.0 / (CONST_oilTemproomTemp)
        steinhart = 1.0 / steinhart
        temperature = steinhart - 273.15  # Convert Kelvin to Celsius
        gaugeItems["OIL_TEMP"][2]=round(temperature,2)
    except:
        gaugeItems["OIL_TEMP"][2]=round(1,2)



#######################
#                     #
#Screen     functions #
#                     #
####################### 

def clearDisplay():
    disp.clear()

def setupDisplay():
    image = Image.new("RGB", (disp.width, disp.height), "BLACK")
    draw = ImageDraw.Draw(image)
    return image,draw

def highlightDisplay(TEXT,hightext):
    drawimage=setupDisplay()
    image=drawimage[0]
    draw=drawimage[1]
    ##(accross screen),(upand down))(100,100 is centre)
    draw.text((70,30),hightext, fill = "WHITE", font=font2)
    draw.text((15,95),TEXT, fill = "WHITE", font =font1)
    im_r=image.rotate(rotation)
    disp.ShowImage(im_r)
    
    
    
#######################
#                     #
#Gauge display        #
#        functions    #
#                     #
####################### 


def value_to_angle(value, min_value, max_value):
    normalized_value = (value - min_value) / (max_value - min_value)
    return ANGLE_START - (ANGLE_START - ANGLE_END) * normalized_value

# Draw the gauge segments
def draw_gauge_segment(draw, start_value, end_value, color, min_value, max_value):
    start_angle = value_to_angle(start_value, min_value, max_value)
    end_angle = value_to_angle(end_value, min_value, max_value)
    draw.arc(
        (CENTER_X - RADIUS, CENTER_Y - RADIUS, CENTER_X + RADIUS, CENTER_Y + RADIUS),
        start=start_angle,
        end=end_angle,
        fill=color,
        width=30  # Increased width
    )

# Draw the gauge needle
def draw_needle(draw, value, min_value, max_value):
    outline_width = 10  # Width of the black outline
    angle = value_to_angle(value, min_value, max_value)
    needle_length = RADIUS - 8  # Adjusted length
    end_x = CENTER_X + needle_length * math.cos(math.radians(angle))
    end_y = CENTER_Y + needle_length * math.sin(math.radians(angle))
    outline_end_x = CENTER_X + (needle_length + 1) * math.cos(math.radians(angle))
    outline_end_y = CENTER_Y + (needle_length + 1) * math.sin(math.radians(angle))
    draw.line((CENTER_X, CENTER_Y, outline_end_x, outline_end_y), fill='white', width=outline_width)
    draw.line((CENTER_X, CENTER_Y, end_x, end_y), fill='red', width=8)

# Draw the value display
def draw_value(draw, value):
    font_large = ImageFont.truetype("arial.ttf", 40)  # Use a larger font size and specify a font
    text = str(value)
    text_bbox = draw.textbbox((0, 0), text, font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (WIDTH - text_width) - 10
    text_y = (HEIGHT - text_height) // 2  # Positioned near the bottom of the image
    draw.text((text_x, text_y), text, fill='white', font=font_large)

# Draw the bottom label
def draw_label(draw, label):
    font_label = ImageFont.truetype("arial.ttf", 25)  # Use a larger font size and specify a font
    label_text = label
    label_bbox = draw.textbbox((0, 0), label_text, font=font_label)
    label_width = label_bbox[2] - label_bbox[0]
    label_height = label_bbox[3] - label_bbox[1]
    label_x = (WIDTH - label_width) // 2
    label_y = HEIGHT - label_height - 65  # Positioned at the bottom of the image
    draw.text((label_x, label_y), label_text, fill='white', font=font_label)

# Function to generate a random value and store it in gaugeItems
def generate_random_value(gauge_key):
    min_value = gaugeItems[gauge_key][7]
    max_value = gaugeItems[gauge_key][8]
    random_value = random.randint(min_value, max_value)
    gaugeItems[gauge_key][2] = random_value


def draw_gauge(gauge_key):
    min_value = gaugeItems[gauge_key][7]
    max_value = gaugeItems[gauge_key][8]
    blue_level = gaugeItems[gauge_key][3]
    green_level = gaugeItems[gauge_key][5]
    red_level = gaugeItems[gauge_key][6]
    label = gaugeItems[gauge_key][1]

    prev_value = min_value

    while True:
        if select_pressed.is_set():
            select_pressed.clear()
            break  # Exit the function to return to the menu


        target_value = gaugeItems[gauge_key][2] *100
        if gauge_key==WIDEBAND02:
                min_value = gaugeItems[gauge_key][7] *100
                max_value = gaugeItems[gauge_key][8] *100
                blue_level = gaugeItems[gauge_key][3] *100
                green_level = gaugeItems[gauge_key][5] *100
                red_level = gaugeItems[gauge_key][6] *100
                target_value = gaugeItems[gauge_key][2] *100
            

            

        # Animate the gauge from the previous value to the new random value
        if target_value > prev_value:
            step = prev_value
            while step <= target_value:
                if select_pressed.is_set():
                    select_pressed.clear()
                    return  # Exit the function to return to the menu

                # Initialize the image and drawing context for each step
                image = Image.new('RGB', (WIDTH, HEIGHT), 'black')
                draw = ImageDraw.Draw(image)

                # Draw the segments
                draw_gauge_segment(draw, min_value, blue_level, 'blue', min_value, max_value)
                draw_gauge_segment(draw, blue_level, green_level, 'green', min_value, max_value)
                draw_gauge_segment(draw, green_level, red_level, 'red', min_value, max_value)
                draw_gauge_segment(draw, red_level, max_value, 'red', min_value, max_value)

                # Draw the black lines at the joins of the colors
                draw_gauge_segment(draw, blue_level, blue_level, 'black', min_value, max_value)
                draw_gauge_segment(draw, green_level, green_level, 'black', min_value, max_value)
                draw_gauge_segment(draw, red_level, red_level, 'black', min_value, max_value)

                # Draw the value display
                draw_value(draw, step)

                # Draw the bottom label
                draw_label(draw, label)

                # Draw the gauge needle
                draw_needle(draw, step, min_value, max_value)

                # Draw a circle at the center of the gauge
                draw.ellipse((CENTER_X - 21, CENTER_Y - 21, CENTER_X + 21, CENTER_Y + 21), fill='white')
                draw.ellipse((CENTER_X - 20, CENTER_Y - 20, CENTER_X + 20, CENTER_Y + 20), fill='black')

                # Show the updated image
                im_r = image.rotate(rotation)
                disp.ShowImage(im_r)

                # Delay to create animation effect
                step += 1
        elif target_value < prev_value:
            step = prev_value
            while step >= target_value:
                if select_pressed.is_set():
                    select_pressed.clear()
                    return  # Exit the function to return to the menu

                # Initialize the image and drawing context for each step
                image = Image.new('RGB', (WIDTH, HEIGHT), 'black')
                draw = ImageDraw.Draw(image)

                # Draw the segments
                draw_gauge_segment(draw, min_value, blue_level, 'blue', min_value, max_value)
                draw_gauge_segment(draw, blue_level, green_level, 'green', min_value, max_value)
                draw_gauge_segment(draw, green_level, red_level, 'red', min_value, max_value)
                draw_gauge_segment(draw, red_level, max_value, 'red', min_value, max_value)

                # Draw the black lines at the joins of the colors
                draw_gauge_segment(draw, blue_level, blue_level, 'black', min_value, max_value)
                draw_gauge_segment(draw, green_level, green_level, 'black', min_value, max_value)
                draw_gauge_segment(draw, red_level, red_level, 'black', min_value, max_value)

                # Draw the value display
                draw_value(draw, step)

                # Draw the bottom label
                draw_label(draw, label)

                # Draw the gauge needle
                draw_needle(draw, step, min_value, max_value)

                # Draw a circle at the center of the gauge
                draw.ellipse((CENTER_X - 21, CENTER_Y - 21, CENTER_X + 21, CENTER_Y + 21), fill='white')
                draw.ellipse((CENTER_X - 20, CENTER_Y - 20, CENTER_X + 20, CENTER_Y + 20), fill='black')

                # Show the updated image
                im_r = image.rotate(rotation)
                disp.ShowImage(im_r)

                # Delay to create animation effect
                step -= 1
        else:
            continue  # If target_value equals prev_value, no animation needed

        # Update the previous value
        prev_value = target_value






#######################
#                     #
#MENU       functions #
#                     #
####################### 


# Button press events
scroll_pressed = threading.Event()
select_pressed = threading.Event()

# Function to draw the menu
def draw_menu(menu_items):
    global menu_indices

    # Create a blank image with background color
    image = Image.new('RGB', (WIDTH, HEIGHT), color=BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    # Calculate vertical position of selected item
    selected_y = HEIGHT // 2 - 25

    # Draw menu items
    for i in range(5):
        # Calculate index of current item
        index = (menu_indices[current_menu] + i - 2) % len(menu_items)

        # Calculate text position
        text = menu_items[index]
        text_color = TEXT_COLOR_SELECTED if i == 2 else TEXT_COLOR_NON_SELECTED1 if i == 1 or i == 3 else TEXT_COLOR_NON_SELECTED2
        text_font = large_font if i == 2 else font if i == 1 or i == 3 else smallfont
        text_bbox = draw.textbbox((0, 0), text, font=text_font)
        x = (WIDTH - text_bbox[2] - text_bbox[0]) // 2
        y = selected_y + (i - 2) * (text_bbox[3] - text_bbox[1] + 20)

        # Draw text for menu items
        draw.text((x, y), text, fill=text_color, font=text_font)

    # Show image on display
    disp.ShowImage(image)

# Function to handle scroll button press
def scroll_callback(channel):
    scroll_pressed.set()

# Function to handle select button press
def select_callback(channel):
    select_pressed.set()

# Add event detection for button presses
GPIO.add_event_detect(SCROLL_PIN, GPIO.FALLING, callback=scroll_callback, bouncetime=300)
GPIO.add_event_detect(SELECT_PIN, GPIO.FALLING, callback=select_callback, bouncetime=300)

# Dummy functions for gauge items
def FUNCT_FUEL_PRESSURE():
    print("Fuel Pressure Function")
    draw_gauge("FUEL_PRESSURE")

def FUNCT_BOOST():
    print("Boost Function")
    draw_gauge("BOOST")

def FUNCT_BLOCK_TEMP():
    print("Engine Temp Function")
    draw_gauge("BLOCK_TEMP")

def FUNCT_COOLANT_PRESSURE():
    print("Coolant Pressure Function")
    draw_gauge("COOLANT_PRESSURE")

def FUNCT_COOLANT_TEMP():
    print("Coolant Temp Function")
    draw_gauge("COOLANT_TEMP")

def FUNCT_OIL_PRESSURE():
    print("Oil Pressure Function")
    draw_gauge("OIL_PRESSURE")

def FUNCT_OIL_TEMP():
    print("Oil Temp Function")
    draw_gauge("OIL_TEMP")

def FUNCT_WIDEBAND02():
    print("O2 AFR Function")
    draw_gauge("WIDEBAND02")

# QUAD_TEMP_GAUGE function
def QUAD_TEMP_GAUGE():
    print("Quad Temp Gauge Function")  # Debug print
    while True:
        if select_pressed.is_set():
            select_pressed.clear()
            break

        oilTemp = gaugeItems["OIL_TEMP"][2]
        coolantTemp = gaugeItems["COOLANT_TEMP"][2]
        blockTemp = gaugeItems["BLOCK_TEMP"][2]
        boost = gaugeItems["BOOST"][2]
        wideband = gaugeItems["WIDEBAND02"][2]

        image = Image.new('RGB', (WIDTH, HEIGHT), color=BACKGROUND_COLOR)
        draw = ImageDraw.Draw(image)

        draw.text((36, 74), "Block Temp", font=smallfont, fill="RED")
        draw.text((45, 30), str(blockTemp) + "°", font=font, fill="WHITE")

        draw.text((145, 74), "Wideband", font=smallfont, fill="RED")
        draw.text((130, 30), str(wideband), font=font, fill="WHITE")

        draw.line([(0, 90), (240, 90)], fill="RED", width=3)

        draw.text((42, 137), "Oil Temp", font=smallfont, fill="RED")
        draw.text((42, 94), str(oilTemp) + "°", font=font, fill="WHITE")

        draw.line([(120, 0), (120, 153)], fill="RED", width=3)

        draw.text((150, 137), "Water Temp", font=smallfont, fill="RED")
        draw.text((155, 94), str(coolantTemp) + "°", font=font, fill="WHITE")

        draw.line([(0, 153), (240, 153)], fill="RED", width=3)

        draw.text((100, 160), "BOOST", font=smallfont, fill="RED")
        draw.text((90, 175), str(boost), font=large_font, fill="WHITE")

        im_r = image.rotate(rotation)
        disp.ShowImage(im_r)
        time.sleep(0.1)

# Function for Triple Stack
def TRIPLE_STACK():
    print("Triple Stack Function")
    while True:
        if select_pressed.is_set():
            select_pressed.clear()
            break
        # Display logic for Triple Stack
        time.sleep(0.1)

# Function to execute gauge function based on selection
def execute_gauge_function(selected_item):
    func_name = "FUNCT_" + selected_item.replace("Pres.","PRESSURE").replace("H2O","Coolant").replace("°C","Temp").replace("Engine","block").replace("O2 AFR", "WIDEBAND02").replace(" ", "_").upper()
        
    if func_name in globals():
        print(f"Executing function: {func_name}")
        globals()[func_name]()
    else:
        print(f"No function found for: {func_name}")


def execute_config_function(selected_item):
    func_name = "FUNCT_" + selected_item.replace(" ", "_").upper()
        
    if func_name in globals():
        print(f"Executing function: {func_name}")
        globals()[func_name]()
    else:
        print(f"No function found for: {func_name}")




#######################
#                     #
#Trouble shooting     #
#    functions        #
#                     #
####################### 

def FUNCT_REBOOT_PI():
    drawimage=setupDisplay()
    image=drawimage[0]
    draw=drawimage[1]
    draw.text((30,85),"REBOOT", font=font1, fill=255)
    draw.text((20,150),"Press button to cancel",font=font2, fill="WHITE")
    tempcount=0
    draw.text((60,30),"..........", font=font1, fill="WHITE")
    im_r=image.rotate(rotation)
    disp.ShowImage(im_r)
    time.sleep(1) 
    
    while tempcount <=10:
        if select_pressed.is_set():
            select_pressed.clear()
            draw_menu(config_menu)
            break
        diedots="."*tempcount
        draw.text((60,30),diedots, font=font1, fill=255)
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        time.sleep(1.5)
        tempcount+=1
        print(tempcount)
    if tempcount == 11:
        os.system('sudo reboot')
  
def getIpAddress():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def FUNCT_IP_ADDRESS():
    IP=getIpAddress()
    highlightDisplay(IP,"Car Guage")
    time.sleep(5)
    draw_menu(config_menu)

def firstBoot():
    disp.Init()
    bootcount=0
    while bootcount <7 :
        bootdots="."*bootcount
        bootext="Booting"+bootdots
        highlightDisplay(bootext,"")
        time.sleep(.3)
        bootcount+=1
    image=Image.open('/home/pi/128_ADCPI/logo.jpg')
    im_r=image.rotate(rotation)
    disp.ShowImage(im_r)
    time.sleep(3)



#######################
#                     #
#Threading  functions #
#                     #
####################### 



def FUNCT_updateValues():
    while True:
#        gaugeItems["BOOST"][2] = random.randint(0, 30)
#        gaugeItems["BLOCK_TEMP"][2] = random.randint(0,400)
#        gaugeItems["FUEL_PRESSURE"][2] = random.randint(0, 150)
#        gaugeItems["OIL_TEMP"][2] = random.randint(0, 400)
#        gaugeItems["COOLANT_TEMP"][2] = random.randint(0, 500)
#        gaugeItems["COOLANT_PRESSURE"][2] = random.randint(0, 150)
#        gaugeItems["OIL_PRESSURE"][2] = random.randint(0, 200)
#        gaugeItems["WIDEBAND02"][2] = (random.randint(0, 389)/100)
        
#        time.sleep(1)
        FUNCT_coolant_pres()   
        FUNCT_coolant_temp()
        FUNCT_oil_pres()
        FUNCT_oil_temp()
        FUNCT_fuel_pres()
        FUNCT_block_temp()
        FUNCT_boost_pres()  
        FUNCT_fuel_pres()
        FUNCT_AFR()



def FUNCT_cliPrint():
    while True:
       os.system('clear')
       print(tabulate([[gaugeItems["BOOST"][2],gaugeItems["FUEL_PRESSURE"][2],gaugeItems["BLOCK_TEMP"][2],gaugeItems["COOLANT_PRESSURE"][2],gaugeItems["COOLANT_TEMP"][2],gaugeItems["OIL_PRESSURE"][2],gaugeItems["OIL_TEMP"][2],gaugeItems["WIDEBAND02"][2]],[]],headers=[gaugeItems["BOOST"][1],gaugeItems["FUEL_PRESSURE"][1],gaugeItems["BLOCK_TEMP"][1],gaugeItems["COOLANT_PRESSURE"][1],gaugeItems["COOLANT_TEMP"][1],gaugeItems["OIL_PRESSURE"][1],gaugeItems["OIL_TEMP"][1],gaugeItems["WIDEBAND02"][1]],  tablefmt='orgtbl'))
       time.sleep(.5)





########################
#                      #
#      Main loop       #
#                      #
########################



firstBoot()
try:
    threading.Thread(target=FUNCT_updateValues).start()
    threading.Thread(target=FUNCT_cliPrint).start()
    while True:
        # Get the current menu items based on the menu state
        if current_menu == "level1":
            menu_items = level1_menu
        elif current_menu == "multigauge":
            menu_items = multigauge_menu
        elif current_menu == "config":
            menu_items = config_menu
        elif current_menu == "gauges":
            menu_items = gauge_menu

        # Draw the current menu
        draw_menu(menu_items)

        # Check for scroll button press
        if scroll_pressed.is_set():
            scroll_pressed.clear()
            menu_indices[current_menu] = (menu_indices[current_menu] + 1) % len(menu_items)

        # Check for select button press
        if select_pressed.is_set():
            select_pressed.clear()

            selected_item = menu_items[menu_indices[current_menu]]
            print(f"Selected item: {selected_item}")  # Debug print

            if selected_item == "Back":
                if current_menu == "multigauge" or current_menu == "config" or current_menu == "gauges":
                    current_menu = "level1"
            elif current_menu == "level1":
                if selected_item == "Gauges":
                    current_menu = "gauges"
                elif selected_item == "MultiGauge":
                    current_menu = "multigauge"
                elif selected_item == "Config":
                    current_menu = "config"
            elif current_menu == "multigauge":
                if selected_item == "QuadTemp":
                    QUAD_TEMP_GAUGE()
                elif selected_item == "Triple Stack":
                    TRIPLE_STACK()
            elif current_menu == "gauges":
                execute_gauge_function(selected_item)
            elif current_menu == "config":
                execute_config_function(selected_item)

            menu_indices[current_menu] = 0

        time.sleep(0.001)

except KeyboardInterrupt:
    GPIO.cleanup()
