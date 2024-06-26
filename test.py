from PIL import Image, ImageDraw, ImageFont
import time
import sys
import threading
import RPi.GPIO as GPIO
sys.path.append('..')

from lib import LCD_1inch28

# Define the menus
level1_menu = ["Gauges", "QuadTemp", "Triple Stack", "Config"]
config_menu = ["ipaddress", "reboot pi", "Back"]
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
gauge_menu = [gaugeItems[key][1] for key in gauge_keys] + ["Back"]

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

# Setup GPIO for buttons
SCROLL_PIN = 38
SELECT_PIN = 40
GPIO.setmode(GPIO.BOARD)
GPIO.setup(SCROLL_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(SELECT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Menu state
current_menu = "level1"
menu_indices = {
    "level1": 0,
    "config": 0,
    "gauges": 0
}
menu_stack = []

# Button press events
scroll_pressed = threading.Event()
select_pressed = threading.Event()

# Function to draw the menu
def draw_menu(menu_items):
    global menu_indices

    # Create a blank image with background color
    image = Image.new('RGB', (WIDTH, HEIGHT), color=BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    # Calculate vertical position of selected item
    selected_y = HEIGHT // 2 - 25

    # Draw menu items
    for i in range(5):
        # Calculate index of current item
        index = (menu_indices[current_menu] + i) % len(menu_items)

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

# Function to handle scroll button press
def scroll_callback(channel):
    scroll_pressed.set()

# Function to handle select button press
def select_callback(channel):
    select_pressed.set()

# Add event detection for button presses
GPIO.add_event_detect(SCROLL_PIN, GPIO.FALLING, callback=scroll_callback, bouncetime=300)
GPIO.add_event_detect(SELECT_PIN, GPIO.FALLING, callback=select_callback, bouncetime=300)

# Main loop
try:
    while True:
        # Get the current menu items based on the menu state
        if current_menu == "level1":
            menu_items = level1_menu
        elif current_menu == "config":
            menu_items = config_menu
        elif current_menu == "gauges":
            menu_items = gauge_menu

        # Draw the current menu
        draw_menu(menu_items)

        # Check for scroll button press
        if scroll_pressed.is_set():
            scroll_pressed.clear()
            menu_indices[current_menu] = (menu_indices[current_menu] + 1) % len(menu_items)

        # Check for select button press
        if select_pressed.is_set():
            select_pressed.clear()
            selected_item = menu_items[menu_indices[current_menu]]

            if selected_item == "Back":
                if menu_stack:
                    previous_menu, previous_index = menu_stack.pop()
                    current_menu = previous_menu
                    menu_indices[current_menu] = previous_index
            else:
                if current_menu == "level1":
                    if selected_item == "Gauges":
                        menu_stack.append((current_menu, menu_indices[current_menu]))
                        current_menu = "gauges"
                    elif selected_item == "QuadTemp":
                        # Call QuadGAUGE function
                        pass
                    elif selected_item == "Triple Stack":
                        # Call TripleGAUGE function
                        pass
                    elif selected_item == "Config":
                        menu_stack.append((current_menu, menu_indices[current_menu]))
                        current_menu = "config"

            # Reset the index for new menu selection
            menu_indices[current_menu] = 0

        # Delay to prevent high CPU usage
        time.sleep(0.1)

finally:
    GPIO.cleanup()
