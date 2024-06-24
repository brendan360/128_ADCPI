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

# Setup GPIO for button
BUTTON_PIN = 36
GPIO.setmode(GPIO.BOARD)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Menu state
current_menu = "level1"
menu_indices = {
    "level1": 0,
    "config": 0,
    "gauges": 0
}
menu_stack = []

# Button press event
button_pressed = threading.Event()

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

# Function to handle button press
def button_callback(channel):
    global current_menu, menu_stack, button_pressed

    button_pressed.set()

    menu_items = []
    if current_menu == "level1":
        menu_items = level1_menu
    elif current_menu == "config":
        menu_items = config_menu
    elif current_menu == "gauges":
        menu_items = gauge_menu

    selected_item = menu_items[menu_indices[current_menu]]

    if selected_item == "Back":
        current_menu = menu_stack.pop() if menu_stack else "level1"
    elif current_menu == "level1":
        if selected_item == "Gauges":
            menu_stack.append(current_menu)
            current_menu = "gauges"
        elif selected_item == "QuadTemp":
            # Call QuadGAUGE function
            pass
        elif selected_item == "Triple Stack":
            # Call TripleGAUGE function
            pass
        elif selected_item == "Config":
            menu_stack.append(current_menu)
            current_menu = "config"

    # Reset the index for new menu selection
    menu_indices[current_menu] = 0

# Add event detection for button press
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_callback, bouncetime=300)

# Main loop
try:
    while True:
        # Scroll menu items until button is pressed
        start_time = time.time()
        while time.time() - start_time < 2:
            # Get the current menu items based on the menu state
            if current_menu == "level1":
                menu_items = level1_menu
            elif current_menu == "config":
                menu_items = config_menu
            elif current_menu == "gauges":
                menu_items = gauge_menu

            # Draw the current menu
            draw_menu(menu_items)

            # Simulate user input (up/down navigation)
            # For real implementation, replace this with actual user input handling
            menu_indices[current_menu] = (menu_indices[current_menu] + 1) % len(menu_items)  # Simulate navigating down the menu

            # Delay for scrolling effect
            time.sleep(0.5)

            # Check if button was pressed
            if button_pressed.is_set():
                button_pressed.clear()
                break

finally:
    GPIO.cleanup()
