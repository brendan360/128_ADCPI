from PIL import Image, ImageDraw, ImageFont
import math
import time
import random
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

prev_value = 0


# Constants for 240x240 screen
WIDTH, HEIGHT = 240, 240
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2
RADIUS = 120  # Increased radius
ANGLE_START, ANGLE_END = 40, 320  # Angles for the 3/4 gauge arc (clockwise)

# Function to convert value to angle
def value_to_angle(value):
    return ANGLE_START - (ANGLE_START - ANGLE_END) * (value / 100)

# Draw the gauge segments
def draw_gauge_segment(draw, start_value, end_value, color):
    start_angle = value_to_angle(start_value)
    end_angle = value_to_angle(end_value)
    if end_angle < start_angle:
        end_angle += 360
    draw.arc(
        (CENTER_X - RADIUS, CENTER_Y - RADIUS, CENTER_X + RADIUS, CENTER_Y + RADIUS),
        start=start_angle,
        end=end_angle,
        fill=color,
        width=30  # Increased width
    )

# Draw the gauge needle
def draw_needle(draw, value):
    outline_width = 10  # Width of the black outline
    angle = value_to_angle(value)
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
    text_width, text_height = draw.textsize(text, font=font_large)
    text_x = (WIDTH - text_width) - 10
    text_y = (HEIGHT - text_height) // 2  # Positioned near the bottom of the image
    draw.text((text_x, text_y), text, fill='white', font=font_large)

# Main loop
while True:
    # Generate a random target value
    target_value = random.randint(0, 100)

    # Animate the gauge from the previous value to the new random value
    step = prev_value
    while step <= target_value:
        # Initialize the image and drawing context for each step
        image = Image.new('RGB', (WIDTH, HEIGHT), 'black')
        draw = ImageDraw.Draw(image)

        # Draw the segments
        draw_gauge_segment(draw, 0, 10, 'blue')
        draw_gauge_segment(draw, 10, 70, 'green')
        draw_gauge_segment(draw, 70, 100, 'red')

        # Draw the gauge needle
        draw_needle(draw, step)
        draw_value(draw, step)

        # Draw a circle at the center of the gauge
        draw.ellipse((CENTER_X - 21, CENTER_Y - 21, CENTER_X + 21, CENTER_Y + 21), fill='white')
        draw.ellipse((CENTER_X - 20, CENTER_Y - 20, CENTER_X + 20, CENTER_Y + 20), fill='black')

        # Show the updated image
        disp.ShowImage(image)

        # Delay to create animation effect
        time.sleep(0.02)  # Adjust the delay for smoother animation

        step += 1

    # Update the previous value
    prev_value = target_value

    # Delay before starting the next cycle
    time.sleep(2)  # Adjust the delay before starting the next cycle
