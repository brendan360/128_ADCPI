from PIL import Image, ImageDraw, ImageFont
import math
import os
import sys
sys.path.append('..')

from lib import LCD_1inch28

RST=27
DC=25
BL=18
bus=0
device = 0
disp = LCD_1inch28.LCD_1inch28()
rotation=180
disp.Init()



image = Image.new('RGB', (240, 240), 'white')
draw = ImageDraw.Draw(image)




center_x, center_y = 120, 120  # Center of the image
radius = 90  # 3/4 of 120 is 90
font_size = 20
font = ImageFont.truetype("arial.ttf", font_size)

# Function to draw the gauge
def draw_gauge(draw, value):
    # Draw the outer circle (gauge boundary)
    draw.arc([center_x - radius, center_y - radius, center_x + radius, center_y + radius], start=0, end=360, fill='black')
    
    # Draw the needle (let's assume value is between 0 to 100)
    angle = (value / 100.0) * 270 - 135  # 270 degrees for 3/4 of the circle, shifted by 135 degrees to start from -135
    end_x = center_x + radius * math.cos(math.radians(angle))
    end_y = center_y + radius * math.sin(math.radians(angle))
    draw.line([center_x, center_y, end_x, end_y], fill='red', width=2)
    
    # Draw the text value
    text = f'{value}%'
    text_width, text_height = draw.textsize(text, font=font)
    text_x = center_x - text_width / 2
    text_y = center_y + radius / 2 - text_height / 2
    draw.text((text_x, text_y), text, fill='black', font=font)

# Example usage
value = 75  # You can change this value to test different positions of the needle
draw_gauge(draw, value)


disp.ShowImage(image)

