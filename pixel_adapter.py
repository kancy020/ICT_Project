import os
import subprocess

# Set base paths
HOME_DIR = os.path.expanduser("~")
IMAGE_DIR = os.path.join(HOME_DIR, "ICT_Project", "emoji_images")
RUN_SCRIPT_PATH = os.path.join(HOME_DIR, "python3-idotmatrix-client", "run_in_venv.sh")

# Set Bluetooth display address
DISPLAY_ADDRESS = "C4:C4:9C:F5:F4:D8"

# Adapter class for controlling the pixel display
class PiAdapter:

    # Display an emoji image from emoji_images directory
    def show_emoji(self, emoji_name, **kwargs):
        image_path = os.path.join(IMAGE_DIR, f"{emoji_name}.png")
        if os.path.exists(image_path):
            try:
                subprocess.run([
                    RUN_SCRIPT_PATH,
                    "--address", DISPLAY_ADDRESS,
                    "--image", "true",
                    "--set-image", image_path
                ], check=True)
                print(f"[✓] Displayed emoji: {emoji_name}")
            except Exception as e:
                print(f"[✗] Failed to show emoji: {e}")
        else:
            print(f"[✗] Image not found: {emoji_name}.png")

    # Display a plain text message
    def show_text(self, message, **kwargs):
        try:
            subprocess.run([
                RUN_SCRIPT_PATH,
                "--address", DISPLAY_ADDRESS,
                "--set-text", message
            ], check=True)
            print(f"[✓] Displayed text: {message}")
        except Exception as e:
            print(f"[✗] Failed to show text: {e}")

# Create and export a global instance
pi_adapter = PiAdapter()
