
#!/usr/bin/python3
#####################
#                   #
#   IMPORTS         #
#                   #
##################### 
from __future__ import absolute_import, division, print_function, unicode_literals
import time
import os
import math
from tabulate import tabulate






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

#PIN CONFIG ROTARY ENCODER ugpio pins
SW = 26
SW1=21
rotaryCounter=0
oldEncValue=0
newEncValue=0
movementValue=0
I2C_ADDR = 0x0F  # 0x18 for IO Expander, 0x0F for the encoder breakout
POT_ENC_A = 12
POT_ENC_B = 3
POT_ENC_C = 11

PIN_RED = 1
PIN_GREEN = 7
PIN_BLUE = 2
BRIGHTNESS = 0.30                # Effectively the maximum fraction of the period that the LED will be on
PERIOD = int(255 / BRIGHTNESS)  # Add a period large enough to get 0-255 steps at the desired brightness
ioe = io.IOE(i2c_addr=I2C_ADDR, interrupt_pin=4)

# Swap the interrupt pin for the Rotary Encoder breakout
if I2C_ADDR == 0x0F:
    ioe.enable_interrupt_out(pin_swap=True)

ioe.setup_rotary_encoder(1, POT_ENC_A, POT_ENC_B, pin_c=POT_ENC_C)
ioe.set_pwm_period(PERIOD)
ioe.set_pwm_control(divider=2)  # PWM as fast as we can to avoid LED flicker
ioe.set_mode(PIN_RED, io.PWM, invert=True)
ioe.set_mode(PIN_GREEN, io.PWM, invert=True)
ioe.set_mode(PIN_BLUE, io.PWM, invert=True)
r, g, b, = 0, 0, 0






#####################
#                   #
#  MENU & DISPLAY   #
#     FUNCTIONS     #
##################### 
topmenu=("Gauges","gaugemenu",,"Config","configmenu","Multi 1","QUAD_GAUGE","","backtotop1")
gaugemenu=("Boost","BOOST","Water °C","COOLANT_TEMP","Water Pres", "COOLANT_PRESSURE","Fuel Pres ","FUEL_PRESSURE","Oil Pres","OIL_PRESSURE","Oil °C","OIL_TEMP","Block °C","BLOCK_TEMP","Wideband","WIDEBAND02" ,"Back","backtotop1")
configmenu=("IP","ipaddress","Reboot","reboot_pi","Back","backtotop3")

#fonts
font = ImageFont.truetype("/home/pi/wrx_gauge/arial.tff", 42)
font2 = ImageFont.truetype("/home/pi/wrx_gauge/arial.tff", 20)
font3 = ImageFont.truetype("/home/pi/wrx_gauge/arial.tff", 12)
gfont = ImageFont.truetype("/home/pi/wrx_gauge/arial.tff", 54)

#Display
disp = LCD_1inch28.LCD_1inch28()
rotation=0
GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SW1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setmode(GPIO.BCM)








#####################
#                   #
#    VARIABLES      #
#                   #
##################### 
 
gaugeItems={
#   NAME,          value, display name warninglow,alertlow,warninghigh,alerthigh,rangelow,rangehigh,measurment,alertcount 
  "FUEL_PRESSURE":["1","Fuel Pres.", 1, 10,15,99,110,0,150,"Kpa", 0],               #
  "BOOST":["2","Boost", 1, 10,15,99,110,0,150,"psi", 0],                       #
  "BLOCK_TEMP":["3","Engine °C ", 1, 10,15,99,110,0,150,"°C", 0],
  "COOLANT_PRESSURE":["4","H2O Pres.", 1, 10,15,99,110,0,150,"Kpa", 0],            
  "COOLANT_TEMP":["5","H2O °C", 1, 10,15,99,110,0,150,"°C", 0],
  "OIL_PRESSURE":["6","Oil Pres.", 1, 10,15,99,110,0,150,"Kpa", 0],                #
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
def menuDisplay(currentMenu,menu):
    drawimage=setupDisplay()
    image=drawimage[0]
    draw=drawimage[1]
    
    if (currentMenu-1 <0):
        minusMenu=(len(menu)-2)
    else:
        minusMenu=currentMenu-2
    
    if (currentMenu+2 >= len(menu)):
        plusMenu=0
    else:
        plusMenu=currentMenu+2

    if (currentMenu+4 == len(menu)):
        plus2Menu=0
        
    elif (currentMenu+4 == (len(menu)+2)):
        plus2Menu=2
    else:
        plus2Menu=currentMenu+4

    if (currentMenu-4 == -1):
        minus2Menu=(len(menu)-2)
    elif (currentMenu-4 == -2):
        minus2Menu=(len(menu)-2)
    else:
        minus2Menu = currentMenu-4
    if (len(menu)/2)>= 5:
        draw.text((35,40), menu[minus2Menu], font=font3, fill="WHITE")
        draw.text((35,190), menu[plus2Menu],font = font3, fill="WHITE")
    
    draw.text((55, 65), menu[minusMenu], font=font2, fill="WHITE")
    draw.text((10, 95),">"+menu[currentMenu], font=font, fill=255)
    draw.text((55, 155), menu[plusMenu], font=font2, fill="WHITE")
    
  
    im_r=image.rotate(rotation)
    disp.ShowImage(im_r)


def menuloop(item,menu):
    def buttonPushed(item,menu):
        doaction(item,menu)
    global newEncValue
    global oldEncValue
    while True:
        if ioe.get_interrupt():
            newEncValue=ioe.read_rotary_encoder(1)
            ioe.clear_interrupt()

            if newEncValue>oldEncValue:
                item-=2
                oldEncValue=newEncValue
            if newEncValue<oldEncValue:
                item+=2
                oldEncValue=newEncValue
            
        if item == (len(menu)):
            item=0
        if item <0:
            item=(len(menu))-2
        
        menuDisplay(item,menu)
        
        buttonState=GPIO.input(SW)
        if buttonState == False:
            doaction(item,menu)

def doaction(item,menu):
    time.sleep(.333)
    if (menu[item]=="Gauges"):
        menuloop(0,gaugemenu)
    if (menu[item] == "Config"):
        menuloop(0,configmenu)
    highlightDisplay("Loading",menu[item])
    print(menu[item+1])
    eval(menu[item+1] + "()")
    
def backtotop1():
    menuloop(0,topmenu)
def backtotop2():
    menuloop(2,topmenu)
def backtotop3():
    menuloop(4,topmenu)








#####################
#                   #
#trouble FUNNCTIONS #
#                   #
##################### 
def firstBoot():
    
#    r, g, b = [int(c * PERIOD * BRIGHTNESS) for c in colorsys.hsv_to_rgb(1.0,1.0,1.0)]
 #   print(r,"   ",g,"   ",b)
    r=255
    g=0
    b=0
    ioe.output(PIN_RED, r)
    ioe.output(PIN_GREEN, g)
    ioe.output(PIN_BLUE, b)
    
    bootcount=0
    while bootcount <7 :
        bootdots="."*bootcount
        bootext="Booting"+bootdots
        highlightDisplay(bootext,"")
        time.sleep(.3)
        bootcount+=1
    image=Image.open('/home/pi/wrx_gauge/logo.jpg')
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
   print(tabulate([[gaugeItems["BOOST"][2]],[gaugeItems["BOOST"][1]]],headers=[gaugeItems["BOOST"][1],[gaugeItems["BOOST"][1]]],tablefmt='orgtbl'))
   os.system('clear')
   print(tabulate([[gaugeItems["BOOST"][2],gaugeItems["FUEL_PRESSURE"][2],gaugeItems["BLOCK_TEMP"][2],gaugeItems["COOLANT_PRESSURE"][2],gaugeItems["COOLANT_TEMP"][2],gaugeItems["OIL_PRESSURE"][2],gaugeItems["OIL_TEMP"][2],gaugeItems["WIDEBAND02"][2]],[]],headers=[gaugeItems["BOOST"][1],gaugeItems["FUEL_PRESSURE"][1],gaugeItems["BLOCK_TEMP"][1],gaugeItems["COOLANT_PRESSURE"][1],gaugeItems["COOLANT_TEMP"][1],gaugeItems["OIL_PRESSURE"][1],gaugeItems["OIL_TEMP"][1],gaugeItems["WIDEBAND02"][1]],  tablefmt='orgtbl'))

def FUNCT_updateValues():
 #    FUNCT_block_temp()
#    FUNCT_boost_pres()  
#    FUNCT_fuel_pres()
    FUNCT_coolant_pres()
#    FUNCT_coolant_temp()
#    FUNCT_oil_pres()
#    FUNCT_oil_temp()
#    FUNCT_fuel_pres()
    FUNCT_cliPrint()
    







#####################
#                   #
#     MAIN          #
#                   #
##################### 
while True:
    FUNCT_updateValues()
    FUNCT_cliPrint()
    time.sleep(.2)


