import subprocess   
import os

# Global mac address for shared use
mac_address = None

# Start_up method triggers commands to start up the pixel display controller
def start_up():
    build_path = ("build.ps1")

    # Returns out of function if path doesnt exist
    if not(os.path.exists("build.ps1")):
        print("build path does not exist")
        return
    
    # Sequence of commands that runs on subprocess
    try:
        results = subprocess.run([
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass", "-File", build_path
            
            ],
                text=True,
                capture_output=True,
                timeout=6
        )

        # Empty print space needed for expected enter input from command
        print("")

        # Error handling for non 0 result
        if results.returncode != 0:
            print(f"Powershell script has failed: {results.stderr}")
        else:
            print("Powershell ran the script successfully")
    
    except subprocess.TimeoutExpired:
        print("PowerShell script timed out")
    except Exception as e:
        print(f"Error running PowerShell script: {e}")


# Using the pixel display controllers scan command to locate scanned mac addresses
def find_mac_address():
    global mac_address 

    mac_command = "python .\\app.py --scan"
    
    try:
        print("Scanning")
        mac = subprocess.run(mac_command, capture_output=True, text=True, shell=True, check=True)

        # Finds the mac address then sets it as the global variable
        mac_address = mac.stdout.strip()
        split_mac_address(mac.stdout, mac.stderr)

        print(mac.stderr)
    
    # Error handling for unable to find mac address
    except subprocess.CalledProcessError as e:
        print(f"Failed to find MAC address: {e}")
        print(f"Error output: {e.stderr}")
        return None
    except Exception as e:
        print(f"Unexpected error finding MAC address: {e}")
        return None
    

# Setting the pixel displays mac address
def set_mac_address():
    global mac_address

    # Return incase setup failed
    if mac_address is None:
        print("No MAC address available. Run find_mac_address() first.")
        return
    
    # Sets the address of the pixel display, which triggers a sync symbol on the pixel display
    address_sync = f"python .\\app.py --address {mac_address}"  

    print(f"The MAC address is: {mac_address}")

    # Command ran in try for error handling
    try:
        address_results = subprocess.run(address_sync, shell=True, check=True, capture_output=True, text=True)
        print("MAC address has been setup for pixel display")
            
    except subprocess.CalledProcessError as e:
        print(f"Failed to set MAC address: {e}")
        print(f"Error output: {e.stderr}")
    except Exception as e:
        print(f"Unexpected error setting MAC address: {e}")


# Slicing the mac_address to find the actual mac address in the sent stderr
def split_mac_address(stout, stderr):
    global mac_address

    if 'found device' in stderr:
        print("found device")
        after_device = stderr.split('found device ')[1]
        mac = after_device.split(' ')[0]  
        if ':' in mac and len(mac) == 17:
            print(mac)
            mac_address = mac
            print(f"is mac address {mac_address}")
            # Returns the full mac_address in upper case
            return mac.upper()
    return None

# Returning the mac address for shared use across classes
def get_mac_address():
    global mac_address
    return mac_address

# Calls the controllers image command to prudice the image to the pixel display
def send_image_to_display(image):
    #  Asessing the global mac address
    global mac_address

    # Setting dir as output
    directory = "output"

    # Removing the colon from emoji texts i.e turning ':smiley_face:' to 'smiley_face'
    image_name = image.replace(":", "")
    image_path = os.path.join(directory, f"{image_name}.png")


    # Returns if path doesnt exist
    if not os.path.exists(image_path):
        print("image does not exist")
        return 
    
    print(f"this is the image_path {image_path}")
    
    set_image_command = f"python .\\app.py --address {mac_address} --image true --set-image {image_path}"
                        
    try:
        # Command ran for image setting to the pixel display, this command finishes the tranfer from back end to pixel display
        result = subprocess.run(set_image_command, shell=True, check=True, capture_output=True, text=True)
        print(f"Image {image} sent to display successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to send image: {e}")


# Command for setting timer time
def set_timer(minutes):
    global mac_address
    
    set_image_command = f"python .\\app.py --address {mac_address} --countdown 1 --countdown-time {minutes}-0"
                        
    try:
        result = subprocess.run(set_image_command, shell=True, check=True, capture_output=True, text=True)
        print(f"Timer is set")
    except subprocess.CalledProcessError as e:
        print(f"Failed to send image: {e}")

# Command for turning off the screen
def turn_screen_off():
    global mac_address
    
    set_image_command = f"python .\\app.py --address {mac_address} --screen off"
                        
    try:
        result = subprocess.run(set_image_command, shell=True, check=True, capture_output=True, text=True)
        print(f"screen is turned off")
    except subprocess.CalledProcessError as e:
        print(f"Failed to turn screen off {e}")

# Command for turning on the screen
def turn_screen_on():
    global mac_address
    
    set_image_command = f"python .\\app.py --address {mac_address} --screen on"
                        
    try:
        result = subprocess.run(set_image_command, shell=True, check=True, capture_output=True, text=True)
        print(f"screen is turned on")
    except subprocess.CalledProcessError as e:
        print(f"Failed to turn screen on {e}")

# Checks if the pixel display is returning a mac address
def check_if_connected():
    global mac_address
    
    if(mac_address == None):
        return "There is no connection to the pixel display!"
    else :
        return "Connected to the pixel display!"

# Sends a help command list to users for command prompts
def command_list():
    help = "Command list --\n" \
           "\n" \
           "The following is all prefixed with the '/emoji' slash command\n" \
           "-------------------------------------------------------------\n" \
           "\n" \
           "send emoji = 😄 or enter *name of emoji*\n" \
           "set timer _(5 represents the timer in minutes)_ = *'timer 5'*\n" \
           "cancel timer = *'cancel timer'*\n" \
           "turn screen off = *'sleep'*\n" \
           "turn screen on = *'awake'*\n" \
           "check status = *'status'*\n" \
           "help commands = *'-h'* or *'-help'*"
    
    return help

    
                        