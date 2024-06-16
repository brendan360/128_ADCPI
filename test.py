#!/usr/bin/python3
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



RST=27
DC=25
BL=18
bus=0
device = 0
disp = LCD_1inch28.LCD_1inch28()
rotation=180


font = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 42)
font2 = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 20)
font3 = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 12)
gfont = ImageFont.truetype("/home/pi/128_ADCPI/arial.ttf", 54)


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


def firstBoot():
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


firstBoot()
