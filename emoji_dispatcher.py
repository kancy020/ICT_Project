import json
import subprocess
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import emoji
import os

# Set key file paths and environment variables
HOME_DIR = os.path.expanduser("~")
RUN_SCRIPT_PATH = os.environ.get("IDOTMATRIX_RUN_SCRIPT", f"{HOME_DIR}/python3-idotmatrix-client/run_in_venv.sh")
FONT_PATH = os.environ.get("EMOJI_FONT_PATH", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
OUTPUT_IMAGE = os.environ.get("EMOJI_OUTPUT_IMAGE", f"{HOME_DIR}/ICT_Project/emoji.png")
CLEANED_IMAGE = os.environ.get("EMOJI_CLEANED_IMAGE", f"{HOME_DIR}/ICT_Project/emoji_final.png")
BLUETOOTH_ADDRESS = os.environ.get("PIXEL_DISPLAY_ADDRESS", "C4:C4:9C:F5:F4:D8")
HISTORY_LOG_PATH = os.path.join(HOME_DIR, "ICT_Project", "emoji_history.json")

# Predefined drawing functions for custom emoji images
def draw_banana(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(6, 3), (10, 3), (13, 6), (12, 9), (9, 12), (5, 12), (3, 10), (4, 7)], fill="yellow")
    draw.ellipse([(5, 2), (11, 4)], fill="gold")

def draw_tea(image):
    draw = ImageDraw.Draw(image)
    draw.rectangle([4, 8, 12, 12], fill="white")
    draw.arc([11, 8, 15, 12], 0, 360, fill="white")
    draw.rectangle([5, 7, 11, 8], fill="brown")

def draw_ok_hand(image):
    draw = ImageDraw.Draw(image)
    draw.polygon([(6, 4), (7, 4), (9, 7), (8, 8), (6, 6), (5, 5)], fill="white")
    draw.rectangle([9, 6, 11, 10], fill="white")

def draw_thumbs_up(image):
    draw = ImageDraw.Draw(image)
    draw.rectangle([7, 5, 9, 11], fill="white")
    draw.rectangle([5, 3, 7, 5], fill="white")

def draw_wave(image):
    draw = ImageDraw.Draw(image)
    draw.arc([3, 3, 13, 13], start=45, end=135, fill="white")
    draw.line([4, 11, 12, 11], fill="white")

custom_draw_functions = {
    "banana": draw_banana,
    "tea": draw_tea,
    "ok_hand": draw_ok_hand,
    "thumbs_up": draw_thumbs_up,
    "wave": draw_wave
}

def emojiname_to_char(name):
    return emoji.emojize(f":{name}:", language="alias")

# Create a 16x16 emoji image, either from custom drawing or font rendering
def create_emoji_image(emoji_char, name, filename=OUTPUT_IMAGE):
    img = Image.new("RGB", (16, 16), color="black")

    if name in custom_draw_functions:
        custom_draw_functions[name](img)
        img.save(filename)
        print(f"[✓] Drawn custom emoji: {name} → {filename}")
        return True

    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(FONT_PATH, 12)
        draw.text((1, 0), emoji_char, font=font, fill="white")
    except Exception as e:
        print(f"[!] Font or render error: {e}")
        return False

    img.save(filename)
    print(f"[✓] Saved emoji image to {filename}")
    return True

# Resize and clean the emoji image for display compatibility
def clean_image_pillow(input_path=OUTPUT_IMAGE, output_path=CLEANED_IMAGE):
    try:
        img = Image.open(input_path).convert("RGB")
        img = img.resize((16, 16), Image.Resampling.NEAREST)
        img.save(output_path, format="PNG", optimize=False)
        print(f"[✓] Cleaned and saved to {output_path}")
        return True
    except Exception as e:
        print(f"[✗] Cleaning failed: {e}")
        return False

# Send the cleaned image to the pixel display over Bluetooth
def send_to_display(image_path=CLEANED_IMAGE):
    command = f"{RUN_SCRIPT_PATH} --address {BLUETOOTH_ADDRESS} --image true --set-image {image_path}"
    print(f"Sending image to pixel display:\n{command}")
    os.system(command)

# Record the emoji usage history to a local JSON log
def log_display_action(content, user="local"):
    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "content": content,
        "user": user
    }

    if os.path.exists(HISTORY_LOG_PATH):
        with open(HISTORY_LOG_PATH, "r") as f:
            history = json.load(f)
    else:
        history = []

    history.append(log_entry)
    with open(HISTORY_LOG_PATH, "w") as f:
        json.dump(history, f, indent=2)

    print(f"[✓] Logged display action: {log_entry}")

# Main function: generate emoji image, process it, display it, and log the action
def dispatch_emoji(name):
    emoji_char = emojiname_to_char(name)
    if not emoji_char or emoji_char == f":{name}:":
        print(f"[✗] Invalid emoji name: {name}")
        return
    print(f"[i] Emoji character: {emoji_char}")

    if create_emoji_image(emoji_char, name) and clean_image_pillow():
        log_display_action(name)
        send_to_display()
    else:
        print("[✗] Failed to generate or clean image.")

if __name__ == "__main__":
    name = input("Enter emoji name (e.g., heart, banana, tea, ok_hand): ").strip()
    dispatch_emoji(name)
