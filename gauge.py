
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
rotation=180



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
 
gaugeItems={
#   NAME,          value, display name warninglow,alertlow,warninghigh,alerthigh,rangelow,rangehigh,measurment,alertcount 
  "FUEL_PRESSURE":["1","Fuel Pres.", 1, 10,15,99,110,0,150,"Kpa", 0],               
  "BOOST":["2","Boost", 1, 10,15,99,110,0,150,"psi", 0],                       
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
    #(x,y)
    oilTemp=gaugeItems["OIL_TEMP"][2]
    coolantTemp=gaugeItems["COOLANT_TEMP"][2]
    blockTemp=gaugeItems["BLOCK_TEMP"][2]
    boost=gaugeItems["BOOST"][2]
    
    drawimage=setupDisplay()
    image=drawimage[0]
    draw=drawimage[1]  

    
    draw.text((26,74),"Block Temp", font=font3,fill="RED")
    if (len(str(blockTemp))==2):
        draw.text((40,30),str(blockTemp)+"°", font=font,fill="WHITE")
    elif (len(str(blockTemp))==3):
        draw.text((33,30),str(blockTemp)+"°", font=font, fill="WHITE")
    else:
        draw.text((48,30),str(blockTemp)+"°", font=font, fill="WHITE")



    draw.line([(0,90),(240,90)],fill="RED", width=3)

    draw.text((25,90),str(oilTemp)+"°",font=font,fill="WHITE")
    draw.text((30,137),"Oil Temp", font=font3,fill="RED")

    draw.line([(120,0),(120,153)],fill="RED", width=3)

    draw.text((145,90),str(coolantTemp)+"°", font=font, fill="WHITE")
    draw.text((150,137),"Water Temp", font=font3,fill="RED")

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

        
        time.sleep(.4)
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
try:
    threading.Thread(target=FUNCT_updateValues).start()
    threading.Thread(target=FUNCT_cliPrint).start()
    threading.Thread(target=QUAD_TEMP_GAUGE).start()
except:
    print("failed starting threads")
#    reboot_pi()
    
