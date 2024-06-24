from PIL import Image, ImageDraw, ImageFont
import time
import sys
sys.path.append('..')

from lib import LCD_1inch28

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

# Colors
BACKGROUND_COLOR = (30, 30, 30)
TEXT_COLOR = (255, 255, 255)
SELECTED_COLOR = (255, 0, 0)
FONT_SIZE = 20

# Fonts
font = ImageFont.truetype("arial.ttf", FONT_SIZE)
large_font = ImageFont.truetype("arial.ttf", FONT_SIZE + 10)

# Initialize starting position for scrolling
start_pos = 0

# Main loop
while True:
    # Create a blank image with background color
    image = Image.new('RGB', (WIDTH, HEIGHT), color=BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    # Calculate vertical position of selected item
    selected_y = HEIGHT // 2

    # Draw menu items
    for i in range(start_pos, start_pos + 5):
        # Get item index (handle wrapping)
        item_index = i % len(gaugeItems)

        # Calculate text size and position
        text_width, text_height = draw.textsize(gaugeItems[item_index][1], font=font)
        x = (WIDTH - text_width) // 2

        # Calculate vertical position of item
        y = selected_y + (i - start_pos - 2) * (text_height + 10)

        # Highlight selected item
        if i == start_pos + 2:
            # Draw selected item in larger font
            draw.text((x, y), gaugeItems[item_index][1], fill=SELECTED_COLOR, font=large_font)
        elif i == start_pos + 1 or i == start_pos + 3:
            # Draw adjacent items with larger font
            draw.text((x, y), gaugeItems[item_index][1], fill=TEXT_COLOR, font=font)
        else:
            # Draw other items with regular font size
            draw.text((x, y), gaugeItems[item_index][1], fill=TEXT_COLOR, font=font)

    # Show image on display
    disp.ShowImage(image)

    # Increment start position for scrolling effect
    start_pos = (start_pos + 1) % len(gaugeItems)

    # Delay for scrolling effect
    time.sleep(0.5)
