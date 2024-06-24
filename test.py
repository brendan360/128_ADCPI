from PIL import Image, ImageDraw, ImageFont
import time
import sys
sys.path.append('..')

from lib import LCD_1inch28

gaugeItems = {
    # NAME: adc read, display name, value, warninglow, alertlow, warninghigh, alerthigh, rangelow, rangehigh, measurement, alertcount 
    "BOOST": ["2", "Boost", 1, 0, -19, 24, 28, -20, 30, "psi", 0],
    "RPM": ["3", "RPM", 500, 0, 100, 5000, 7000, 0, 8000, "rpm", 0],
    "TEMP": ["4", "Temp", 80, 60, 70, 100, 110, 0, 120, "C", 0],
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

# Draw the menu
def draw_menu(selected_index):
    image = Image.new('RGB', (WIDTH, HEIGHT), 'black')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("arial.ttf", 24)

    # Calculate positions for menu items
    menu_items = list(gaugeItems.keys())
    num_items = len(menu_items)
    item_height = HEIGHT // num_items

    for i, key in enumerate(menu_items):
        text = gaugeItems[key][1]  # Display name of the gauge item
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Center the text horizontally
        text_x = (WIDTH - text_width) // 2
        text_y = i * item_height + (item_height - text_height) // 2

        if i == selected_index:
            # Highlight the selected menu item
            draw.rectangle([0, i * item_height, WIDTH, (i + 1) * item_height], outline='white', width=2)
            draw.text((text_x, text_y), text, fill='yellow', font=font)
        else:
            draw.text((text_x, text_y), text, fill='white', font=font)

    disp.ShowImage(image)

# Function to handle the menu scrolling
def scroll_menu():
    selected_index = 0
    menu_items = list(gaugeItems.keys())
    num_items = len(menu_items)
    
    draw_menu(selected_index)

    while True:
        # Simulate button presses for scrolling (up and down)
        # This is just an example. Replace with actual button press logic
        time.sleep(1)  # Wait for 1 second before changing selection
        selected_index = (selected_index + 1) % num_items
        draw_menu(selected_index)

        # Simulate selection
        time.sleep(1)
        # Perform action for selected menu item
        selected_key = menu_items[selected_index]
        print(f"Selected: {selected_key}")

# Call the scroll menu function
scroll_menu()
