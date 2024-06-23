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

WIDTH, HEIGHT = 240, 240
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2
RADIUS = 180
ANGLE_START, ANGLE_END =  135, -135  # Angles for the gauge arc
VALUE =50  # Example value to display on the gauge

# Create a blank image with a white background
image = Image.new('RGB', (WIDTH, HEIGHT), 'white')
draw = ImageDraw.Draw(image)

# Function to convert value to angle
def value_to_angle(value):
    return ANGLE_START + (ANGLE_END - ANGLE_START) * (value / 100)

# Draw the circular frame for the round screen
draw.ellipse((CENTER_X - RADIUS - 10, CENTER_Y - RADIUS - 10, CENTER_X + RADIUS + 10, CENTER_Y + RADIUS + 10), outline='black', width=5)

# Draw the gauge segments
def draw_gauge_segment(start_value, end_value, color):
    start_angle = value_to_angle(start_value)
    end_angle = value_to_angle(end_value)
    draw.arc(
        (CENTER_X - RADIUS, CENTER_Y - RADIUS, CENTER_X + RADIUS, CENTER_Y + RADIUS),
        start=start_angle,
        end=end_angle,
        fill=color,
        width=20
    )

# Draw the segments
draw_gauge_segment(0, 10, 'blue')
draw_gauge_segment(10, 70, 'green')
draw_gauge_segment(70, 100, 'red')

# Draw the gauge needle
angle = value_to_angle(VALUE)
needle_length = RADIUS - 20
end_x = CENTER_X + needle_length * math.cos(math.radians(angle))
end_y = CENTER_Y + needle_length * math.sin(math.radians(angle))
draw.line((CENTER_X, CENTER_Y, end_x, end_y), fill='red', width=5)

# Draw a circle at the center of the gauge
draw.ellipse((CENTER_X - 10, CENTER_Y - 10, CENTER_X + 10, CENTER_Y + 10), fill='black')

# Optionally, draw tick marks and labels
for i in range(0, 101, 10):
    angle = value_to_angle(i)
    outer_x = CENTER_X + (RADIUS - 5) * math.cos(math.radians(angle))
    outer_y = CENTER_Y + (RADIUS - 5) * math.sin(math.radians(angle))
    inner_x = CENTER_X + (RADIUS - 25) * math.cos(math.radians(angle))
    inner_y = CENTER_Y + (RADIUS - 25) * math.sin(math.radians(angle))
    draw.line((inner_x, inner_y, outer_x, outer_y), fill='black', width=2)
    
    # Draw the labels
    font = ImageFont.load_default()
    label_x = CENTER_X + (RADIUS - 40) * math.cos(math.radians(angle))
    label_y = CENTER_Y + (RADIUS - 40) * math.sin(math.radians(angle))
    draw.text((label_x - 10, label_y - 10), str(i), fill='black', font=font)

# Draw the value display
font_large = ImageFont.truetype("arial.ttf", 40)  # Use a larger font size and specify a font
text = str(VALUE)
text_width, text_height = draw.textsize(text, font=font_large)
text_x = (WIDTH - text_width) // 2
text_y = HEIGHT - text_height - 20  # Positioned near the bottom of the image
draw.text((text_x, text_y), text, fill='black', font=font_large)

disp.ShowImage(image)

