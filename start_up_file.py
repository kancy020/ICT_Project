import subprocess
import emoji_list
import time

def start_up_pixel_display():
    command = ["./run_in_venv.sh <YOUR_COMMAND_LINE_ARGUMENTS>"
               "./run_in_venv_sh auto",
               "./run_in_venv.sh --scan",
               "./run_in_venv.sh --address 00:11:22:33:44:ff --sync-time",
               "./run_in_venv.sh --address 00:11:22:33:44:ff --screen on",
               "./run_in_venv_sh --address 00:11:22:33:44:ff --image true",
               "./run_in_venv_sh --address 00:11:22:33:44:ff --image true --set-image ./"
               ]
    
    try:
        subprocess(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"failed to sync pixel display")

    
def send_image_to_display(emoji):
    img_path = emoji_list.get_path(emoji)    

    set_image_command = ["./run_in_venv.sh",
                            "--address",
                            "--image", "true",
                            "--set-image", img_path
                            ]
    
    try:
        subprocess.run(set_image_command, check=True)
        print(f"Image {img_path} sent to display successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to send image: {e}")