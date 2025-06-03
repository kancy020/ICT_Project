import subprocess   



def start_up():
    build_path = (".\\build.ps1")

    subprocess.run([
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", build_path], 

        input="y\n",
        text = True
        
    )

    print("")


def find_mac_address():
    global mac_address

    mac_command = "python app.py --scan"

    mac = subprocess.run(mac_command, capture_output=True, text=True, shell=True, check=True)

    print(f"mac address is: {mac}")
    


# def send_image_to_display(emoji):
#     img_path = emoji_list.get_path(emoji)    

#     set_image_command = ["./run_in_venv.sh",
#                             "--address",
#                             "--image", "true",
#                             "--set-image", img_path
#                             ]
    
#     try:
#         subprocess.run(set_image_command, check=True)
#         print(f"Image {img_path} sent to display successfully.")
#     except subprocess.CalledProcessError as e:
#         print(f"Failed to send image: {e}")


if __name__ == "__main__":
    start_up()
    print("start pixel display")
