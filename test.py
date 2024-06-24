from PIL import Image, ImageDraw, ImageFont
import time
import sys
sys.path.append('..')

from lib import LCD_1inch28

# Define the menus
level1_menu = ["Gauges", "QuadTemp", "Triple Stack", "Config"]
config_menu = ["ipaddress", "reboot pi"]
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

# Define colors
BACKGROUND_COLOR = (30, 30, 30)
TEXT_COLOR_SELECTED = (255, 0, 0)
TEXT_COLOR_NON_SELECTED1 = (255, 255, 255)  # White
TEXT_COLOR_NON_SELECTED2 = (0, 0, 255)      # Blue
FONT_SIZE = 30

# Define fonts
font = ImageFont.truetype("arial.ttf", FONT_SIZE)
smallfont = ImageFont.truetype("arial.ttf", FONT_SIZE - 10)
large_font = ImageFont.truetype("arial.ttf", FONT_SIZE + 14)

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

# Menu state
current_menu = "gauges"
current_index = 0

# Main loop
while True:
    # Create a blank image with background color
    image = Image.new('RGB', (WIDTH, HEIGHT), color=BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    # Get the current menu items based on the menu state
    if current_menu == "level1":
        menu_items = level1_menu
    elif current_menu == "config":
        menu_items = config_menu
    elif current_menu == "gauges":
        menu_items = [gaugeItems[key][1] for key in gauge_keys]
    
    # Calculate vertical position of selected item
    selected_y = HEIGHT // 2 - 25

    # Draw menu items
    for i in range(5):
        # Calculate index of current item
        index = (current_index + i) % len(menu_items)

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

    # Increment current index for scrolling effect
    current_index = (current_index + 1) % len(menu_items)

    # Delay for scrolling effect
    time.sleep(0.5)
