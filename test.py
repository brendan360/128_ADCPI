from PIL import Image, ImageDraw, ImageFont
import time
import sys
import math
sys.path.append('..')

from lib import LCD_1inch28

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

# Define colors
BACKGROUND_COLOR = (30, 30, 30)
TEXT_COLOR_SELECTED = (255, 0, 0)
TEXT_COLOR_NON_SELECTED1 = (255, 255, 255)  # White
TEXT_COLOR_NON_SELECTED2 = (0, 0, 255)      # Blue
FONT_SIZE = 24

# Define fonts
font = ImageFont.truetype("arial.ttf", FONT_SIZE)
smallfont = ImageFont.truetype("arial.ttf", FONT_SIZE - 10)
large_font = ImageFont.truetype("arial.ttf", FONT_SIZE + 20)

# Initialize display
RST = 27
DC = 25
BL = 18
bus = 0
device = 0
disp = LCD_1inch28.LCD_1inch28()
rotation = 180
disp.Init()

# Constants for 240x240 screen
WIDTH, HEIGHT = 240, 240

# Initialize starting position for scrolling
start_pos = 0

# Main loop
while True:
    # Create a blank image with background color
    image = Image.new('RGB', (WIDTH, HEIGHT), color=BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    # Calculate vertical position of selected item
    selected_y = HEIGHT // 2 - 20

    # Draw menu items
    for i in range(6):  # Include space for the "Back" item
        # Calculate index of current item
        if i == 5:
            text = "Back"
            text_color = TEXT_COLOR_SELECTED if i == 2 else TEXT_COLOR_NON_SELECTED1
            text_font = large_font if i == 2 else font
        else:
            index = (start_pos + i) % len(gaugeItems)
            text = gaugeItems[list(gaugeItems.keys())[index]][1]
            text_color = TEXT_COLOR_SELECTED if i == 2 else TEXT_COLOR_NON_SELECTED1 if i == 1 or i == 3 else TEXT_COLOR_NON_SELECTED2
            text_font = large_font if i == 2 else font if i == 1 or i == 3 else smallfont

        # Calculate text position
        text_bbox = draw.textbbox((0, 0), text, font=text_font)
        x = (WIDTH - text_bbox[2] - text_bbox[0]) // 2
        y = selected_y + (i - 2) * (text_bbox[3] - text_bbox[1] + 10)

        # Draw text for menu items
        draw.text((x, y), text, fill=text_color, font=text_font)

    # Show image on display
    disp.ShowImage(image)

    # Increment start position for scrolling effect
    start_pos = (start_pos + 1) % len(gaugeItems)

    # Delay for scrolling effect
    time.sleep(0.5)
