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
sys.path.append('..')
from lib import LCD_1inch28
from PIL import Image, ImageDraw, ImageFont
import spidev as SPI
import colorsys
import signal
import spidev as SPI
import threading
import random


#####################
#                   #
#    SETUPS         #
#                   #
##################### 

######setting up adc board
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



#######Setting up lcd

RST=27
DC=25
BL=18
bus=0
device = 0
disp = LCD_1inch28.LCD_1inch28()
rotation=0

# Constants for 240x240 screen
WIDTH, HEIGHT = 240, 240
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2
RADIUS = 120  # Increased radius
ANGLE_START, ANGLE_END = 40, 320  # Angles for the 3/4 gauge arc (clockwise)



#####################
#                   #
#  MENU & fonts     #
#     FUNCTIONS     #
##################### 
topmenu=("Gauges","gaugemenu","Config","configmenu","Multi 1","QUAD_GAUGE","backtotop1")
gaugemenu=("Boost","BOOST","Water °C","COOLANT_TEMP","Water Pres", "COOLANT_PRESSURE","Fuel Pres ","FUEL_PRESSURE","Oil Pres","OIL_PRESSURE","Oil °C","OIL_TEMP","Block °C","BLOCK_TEMP","Wideband","WIDEBAND02" ,"Back","backtotop1")
configmenu=("IP","ipaddress","Reboot","reboot_pi","Back","backtotop3")


#fonts
font = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 42)
font2 = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 20)
font3 = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 12)
gfont = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 54)



#####################
#                   #
#    VARIABLES      #
#                   #
##################### 
 
gaugeItems = {
    # NAME: adc read, display name, value, warninglow, alertlow, warninghigh, alerthigh, rangelow, rangehigh, measurement, alertcount
  "FUEL_PRESSURE":["1","Fuel Pres.", 1, 10,15,99,110,0,150,"Kpa", 0],          
  "BOOST": ["2", "Boost", 1, 0, -19, 24, 28, -20, 30, "psi", 0],
  "BLOCK_TEMP":["3","Engine °C ", 1, 10,15,99,110,0,150,"°C", 0],
  "COOLANT_PRESSURE":["4","H2O Pres.", 1, 10,15,99,110,0,150,"Kpa", 0],            
  "COOLANT_TEMP":["5","H2O °C", 1, 10,15,99,110,0,150,"°C", 0],
  "OIL_PRESSURE":["6","Oil Pres.", 1, 10,15,99,110,0,150,"Kpa", 0],                
  "OIL_TEMP":["7","Oil °C", 1, 10,15,99,110,0,150,"°C", 0],
  "WIDEBAND02":["8","O2 AFR", 1, 10,15,99,110,0,150,"A/F", 0]
}



#####################
#                   #
#SENSOR CONSTANT    #
#                   #
##################### 
CONST_supply_voltage =4.7

CONST_fuel_minVoltage =.48
CONST_fuel_maxVoltage =4.5
CONST_fuel_minPressure =0
CONST_fuel_maxPressure =1000

CONST_coolant_minVoltage =.31
CONST_coolant_maxVoltage =4.5
CONST_coolant_minPressure =0
CONST_coolant_maxPressure =1000

CONST_oil_minVoltage =.5
CONST_oil_maxVoltage =4.5
CONST_oil_minPressure =0
CONST_oil_maxPressure =1000

CONST_boost_minVoltage =.4
CONST_boost_maxVoltage =4.65
CONST_boost_minPressure =20
CONST_boost_maxPressure =300

CONST_blockTemp_balanceResistor = 1000.0
CONST_blockTemp_beta = 3600
CONST_blockTemproomTemp = 298.15 
CONST_blockTempresistorRoomTemp =3000 

CONST_coolantTemp_balanceResistor = 1000.0
CONST_coolantTemp_beta = 3446
CONST_coolantTemproomTemp = 293.15
CONST_coolantTempresistorRoomTemp = 2480.0

CONST_oilTemp_balanceResistor = 1000.0
CONST_oilTemp_beta = 3446
CONST_oilTemproomTemp = 293.15
CONST_oilTempresistorRoomTemp = 2480.0

CONST_AFR_minVoltage=.68
CONST_AFT_maxVoltage=1.36




#######################
#                     #
#Calculator functions #
#                     #
####################### 
def FUNCT_fuel_pres():
    voltage=adc.read_voltage(int(gaugeItems["FUEL_PRESSURE"][0]))
    gaugeItems["FUEL_PRESSURE"][2]= (voltage - CONST_fuel_minVoltage)/(CONST_fuel_maxVoltage -CONST_fuel_minVoltage)*(CONST_fuel_maxPressure- CONST_fuel_minPressure) + CONST_fuel_minPressure

def FUNCT_coolant_pres():
    cvoltage=adc.read_voltage(int(gaugeItems["COOLANT_PRESSURE"][0]))
    gaugeItems["COOLANT_PRESSURE"][2]= (cvoltage - CONST_coolant_minVoltage)/(CONST_coolant_maxVoltage - CONST_coolant_minVoltage)*(CONST_coolant_maxPressure- CONST_coolant_minPressure) + CONST_coolant_minPressure
            
def FUNCT_oil_pres():
    voltage=adc.read_voltage(int(gaugeItems["OIL_PRESSURE"][0]))
    gaugeItems["OIL_PRESSURE"][2]= (voltage - CONST_oil_minVoltage)/(CONST_oil_maxVoltage -CONST_oil_minVoltage)*(CONST_oil_maxPressure- CONST_oil_minPressure) + CONST_oil_minPressure

def FUNCT_boost_pres():
    voltage=adc.read_voltage(int(gaugeItems["BOOST"][0]))
    boostKpa= (voltage - CONST_boost_minVoltage)/(CONST_boost_maxVoltage -CONST_boost_minVoltage)*(CONST_boost_maxPressure- CONST_boost_minPressure) + CONST_boost_minPressure
    gaugeItems["BOOST"][2]=round(((boostKpa-91.3)*0.145038),2)
    if gaugeItems["BOOST"][2] < 0:
        gaugeItems["BOOST"][9] = "inHg"
        gaugeItems["BOOST"][2]=round((abs(gaugeItems["BOOST"][2])*2.03602),2)
    else:
        gaugeItems["BOOST"][9] = "psi"

def FUNCT_block_temp():
    voltage=adc.read_voltage(int(gaugeItems["BLOCK_TEMP"][0]))
    voltage=CONST_blockTemp_balanceResistor/voltage
    steinhart = voltage /CONST_blockTempresistorRoomTemp 
    steinhart = math.log(steinhart) 
    steinhart /=CONST_blockTemp_beta
    steinhart += 1.0 / (CONST_blockTemproomTemp)
    steinhart = 1.0 / steinhart
    steinhart -= 273.15
    gaugeItems["BLOCK_TEMP"][2]=round(steinhart,2)

def FUNCT_coolant_temp():
    voltage=adc.read_voltage(int(gaugeItems["COOLANT_TEMP"][0]))
    resistance = CONST_coolantTemp_balanceResistor / (CONST_supply_voltage / voltage - 1)
    steinhart = resistance / CONST_coolantTempresistorRoomTemp
    steinhart = math.log(steinhart)
    steinhart /= CONST_coolantTemp_beta
    steinhart += 1.0 / (CONST_coolantTemproomTemp)
    steinhart = 1.0 / steinhart
    temperature = steinhart - 273.15  # Convert Kelvin to Celsius
    gaugeItems["COOLANT_TEMP"][2]=round(temperature,2)

def FUNCT_oil_temp():
    voltage=adc.read_voltage(int(gaugeItems["OIL_TEMP"][0]))
    resistance = CONST_oilTemp_balanceResistor / (CONST_supply_voltage / voltage - 1)
    steinhart = resistance / CONST_oilTempresistorRoomTemp
    steinhart = math.log(steinhart)
    steinhart /= CONST_oilTemp_beta
    steinhart += 1.0 / (CONST_oilTemproomTemp)
    steinhart = 1.0 / steinhart
    temperature = steinhart - 273.15  # Convert Kelvin to Celsius
    gaugeItems["OIL_TEMP"][2]=round(temperature,2)








#####################
#                   #
#DISPLAY FUNCTIONS  #
#                   #
##################### 



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
    draw.text((15,95),TEXT, fill = "WHITE", font =font)
    im_r=image.rotate(rotation)
    disp.ShowImage(im_r)

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
    font_large = ImageFont.truetype("arial.ttf", 45)  # Use a larger font size and specify a font
    text = str(value)
    text_bbox = draw.textbbox((0, 0), text, font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = (WIDTH - text_width) - 10
    text_y = (HEIGHT - text_height) // 2  # Positioned near the bottom of the image
    draw.text((text_x, text_y), text, fill='white', font=font_large)

# Draw the bottom label
def draw_label(draw, label):
    font_label = ImageFont.truetype("arial.ttf", 24)  # Use a larger font size and specify a font
    label_text = label
    label_bbox = draw.textbbox((0, 0), label_text, font=font_label)
    label_width = label_bbox[2] - label_bbox[0]
    label_height = label_bbox[3] - label_bbox[1]
    label_x = (WIDTH - label_width) // 2
    label_y = HEIGHT - label_height - 50  # Positioned at the bottom of the image
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
        # Generate a new random value
        generate_random_value(gauge_key)
        target_value = gaugeItems[gauge_key][2]

        # Animate the gauge from the previous value to the new random value
        if target_value > prev_value:
            step = prev_value
            while step <= target_value:
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
                disp.ShowImage(image)

                # Delay to create animation effect
                time.sleep(0.02)  # Adjust the delay for smoother animation

                step += 1
        elif target_value < prev_value:
            step = prev_value
            while step >= target_value:
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
                disp.ShowImage(image)

                # Delay to create animation effect
                time.sleep(0.02)  # Adjust the delay for smoother animation

                step -= 1
        else:
            continue  # If target_value equals prev_value, no animation needed

        # Update the previous value
        prev_value = target_value

#####################
#                   #
#menu FUNCTIONS     #
#                   #
##################### 



#####################
#                   #
#   Gauge Display   #
#   FUNCTIONS       #
#                   #
##################### 
def QUAD_TEMP_GAUGE():
    while True:
        #(x,y)
        oilTemp=gaugeItems["OIL_TEMP"][2]
        coolantTemp=gaugeItems["COOLANT_TEMP"][2]
        blockTemp=gaugeItems["BLOCK_TEMP"][2]
        boost=gaugeItems["BOOST"][2]
        wideband=gaugeItems["WIDEBAND02"][2]
    
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]  
   
        draw.text((36,74),"Block Temp", font=font3,fill="RED")
        if (len(str(blockTemp))==2):
            draw.text((45,30),str(blockTemp)+"°", font=font,fill="WHITE")
        elif (len(str(blockTemp))==3):
            draw.text((33,30),str(blockTemp)+"°", font=font, fill="WHITE")
        else:
            draw.text((58,30),str(blockTemp)+"°", font=font, fill="WHITE")

        draw.text((145,74),"Wideband", font=font3,fill="RED")
        draw.text((130,30),str(wideband), font=font, fill="WHITE")

        
        draw.line([(0,90),(240,90)],fill="RED", width=3)

        
        draw.text((42,137),"Oil Temp", font=font3,fill="RED")
        if (len(str(oilTemp))==2):
            draw.text((42,94),str(oilTemp)+"°", font=font,fill="WHITE")
        elif (len(str(oilTemp))==3):
            draw.text((25,94),str(oilTemp)+"°", font=font, fill="WHITE")
        else:
            draw.text((52,94),str(oilTemp)+"°", font=font, fill="WHITE")

        
        draw.line([(120,0),(120,153)],fill="RED", width=3)

        
        draw.text((150,137),"Water Temp", font=font3,fill="RED")      
        if (len(str(coolantTemp))==2):
            draw.text((155,94),str(coolantTemp)+"°", font=font,fill="WHITE")
        elif (len(str(coolantTemp))==3):
            draw.text((145,94),str(coolantTemp)+"°", font=font, fill="WHITE")
        else:
            draw.text((160,94),str(coolantTemp)+"°", font=font, fill="WHITE")
      

        draw.line([(0,153),(240,153)],fill="RED", width=3)

        
        draw.text((100,160),"BOOST",font=font3,fill="RED")
        if (len(str(boost))==2):
            draw.text((90,175),str(boost), font=gfont,fill="WHITE")
        elif (len(str(boost))==3):
            draw.text((80,175),str(boost), font=gfont, fill="WHITE")
        else:
            draw.text((105,175),str(boost), font=gfont, fill="WHITE")
        
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)

def Triple_GAUGE():
        boost=gaugeItems["BOOST"][2]
        wideband=gaugeItems["WIDEBAND02"][2]
        oilTemp=gaugeItems["OIL_TEMP"][2]
    
        drawimage=setupDisplay()
        image=drawimage[0]
        draw=drawimage[1]  




#####################
#                   #
#trouble FUNNCTIONS #
#                   #
##################### 
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

    
def reboot_pi():
    drawimage=setupDisplay()
    image=drawimage[0]
    draw=drawimage[1]
    draw.text((30,85),"REBOOT", font=font, fill=255)
    draw.text((20,150),"Press button to cancel",font=font2, fill="WHITE")
    tempcount=0
    draw.text((60,30),"..........", font=font, fill="WHITE")
    im_r=image.rotate(rotation)
    disp.ShowImage(im_r)
    time.sleep(5) 
    
    while tempcount <=10:
        buttonState=GPIO.input(SW)
        if buttonState == False:
            menuloop(4,topmenu)
        diedots="."*tempcount
        draw.text((60,30),diedots, font=font, fill=255)
        im_r=image.rotate(rotation)
        disp.ShowImage(im_r)
        time.sleep(1)
        tempcount+=1

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

def ipaddress():
    IP=getIpAddress()
    highlightDisplay(IP,"Car Guage")
    time.sleep(5)
    menuloop(0,configmenu)



#####################
#                   #
#SUBMAIN FUNCTIONS  #
#                   #
##################### 
def FUNCT_cliPrint():
    while True:

       os.system('clear')
       print(tabulate([[gaugeItems["BOOST"][2],gaugeItems["FUEL_PRESSURE"][2],gaugeItems["BLOCK_TEMP"][2],gaugeItems["COOLANT_PRESSURE"][2],gaugeItems["COOLANT_TEMP"][2],gaugeItems["OIL_PRESSURE"][2],gaugeItems["OIL_TEMP"][2],gaugeItems["WIDEBAND02"][2]],[]],headers=[gaugeItems["BOOST"][1],gaugeItems["FUEL_PRESSURE"][1],gaugeItems["BLOCK_TEMP"][1],gaugeItems["COOLANT_PRESSURE"][1],gaugeItems["COOLANT_TEMP"][1],gaugeItems["OIL_PRESSURE"][1],gaugeItems["OIL_TEMP"][1],gaugeItems["WIDEBAND02"][1]],  tablefmt='orgtbl'))
       time.sleep(.5)

def FUNCT_updateValues():
    while True:
        gaugeItems["BOOST"][2] = random.randint(0, 40)
        gaugeItems["BLOCK_TEMP"][2] = random.randint(0,400)
        gaugeItems["FUEL_PRESSURE"][2] = random.randint(0, 150)
        gaugeItems["OIL_TEMP"][2] = random.randint(0, 400)
        gaugeItems["COOLANT_TEMP"][2] = random.randint(0, 500)
        gaugeItems["COOLANT_PRESSURE"][2] = random.randint(0, 150)
        gaugeItems["OIL_PRESSURE"][2] = random.randint(0, 200)
        gaugeItems["WIDEBAND02"][2] = (random.randint(0, 389)/100)
        
        time.sleep(2)
#    FUNCT_coolant_pres()   
#    FUNCT_coolant_temp()
#    FUNCT_oil_pres()
#    FUNCT_oil_temp()
#    FUNCT_fuel_pres()
#    FUNCT_block_temp()
#    FUNCT_boost_pres()  
#    FUNCT_fuel_pres()
    

    







#####################
#                   #
#     MAIN          #
#                   #
##################### 
firstBoot()
#try:
threading.Thread(target=FUNCT_updateValues).start()
  #  threading.Thread(target=FUNCT_cliPrint).start()
threading.Thread(target=draw_gauge, args=("BOOST",)).start()
#except:
 #   print("failed starting threads")
#    reboot_pi()
    
