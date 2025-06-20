import os
from flask import Flask, request, Response, jsonify
import requests
import emoji
import subprocess
import Zhuanhuan
from slack_sdk import WebClient
import start_up_file
import threading
import time

# —— inject admin modules
from admin_panel.managers.admin_manager      import AdminManager
from admin_panel.managers.interface_manager  import interface_manager
from admin_panel.managers.task_queue        import TaskQueueManager
from admin_panel.managers.user_manager       import UserManager
from admin_panel.managers.device_manager     import DeviceManager


#Initialising the Flask application
app = Flask(__name__)

# —— inject admin & subsystems initialization
device_mgr     = DeviceManager()
taskq_mgr      = TaskQueueManager()
user_mgr       = UserManager()
admin_mgr      = AdminManager(port=9999)
admin_mgr.set_components(
    interface_manager,
    taskq_mgr,
    user_mgr,
    device_mgr
)



#class to hold enum values of system state
class State():
     ON = 1
     OFF = 2
     TIMER = 3


# Initializing the status as ON for app entry
status = State.ON
mac_address = start_up_file.mac_address


# Slack bot token which establishes connection to the slack api's event subscription, needed for obtaining images for custom emojis
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)


# Obtains the image from the custom emoji aswell as client emojis through the slash command, sends it to the input file and then process continues to the output images
def get_emoji_url(emoji_name):
    name_e = emoji_name.replace(":", "")
    
    # Ensure input directory exists
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    # Finding the emoji using get_emoji_url function that adds emoji to input folder
    try:
        # Grabs emoji alies name
        emoji_char = emoji.emojize(emoji_name, language="alias")
        # If it find the name search for the png using the get_standard_emoji call
        if emoji_char != emoji_name:
            url = get_standard_emoji_url(emoji_char)
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # Raises exception for bad status codes
                
                # Adding newly found emoji file to input folder which adds it as a png
                with open(f"input/{name_e}.png", "wb") as file:
                    file.write(response.content)
                
                # processed the file with the new name as a 16 x 16 pixel png which gets added to output folder
                Zhuanhuan.batch_process_single_file(name_e)
                return url
            except requests.RequestException as e:
                print(f"Failed to download standard emoji: {e}")
    except Exception as e:
        print(f"Standard emoji processing failed: {e}")

    
    # For customer emojis retrieves it from the slack client
    try:
        # Finds custom emoji
        emoji_list = client.emoji_list()
        emoji_dict = emoji_list.get("emoji", {})
        url = emoji_dict.get(name_e)
        
        if url:
            # Handle aliases
            if url.startswith("alias:"):
                alias = url.split("alias:")[1]
                return get_emoji_url(f":{alias}:")
            
            # Download custom emoji from slack client
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                with open(f"input/{name_e}.png", "wb") as f:
                    f.write(response.content)
                
                Zhuanhuan.batch_process_single_file(name_e)
                return url
            except requests.RequestException as e:
                print(f"Failed to download custom emoji: {e}")
    except Exception as e:
        print(f"Custom emoji processing failed: {e}")
    return None


#Endpoint to which the slack events are received which are cnnected via a challenge request response
@app.route('/slack/events', methods=['POST'])
def slack_events():    
    payload = request.get_json()

    #The challenge request prompted by URL to slack server
    if "challenge" in payload:
        return jsonify({"challenge": payload["challenge"]})
    
    return Response(), 200


#This POST method houses the main features of the program through the slack command intergration
@app.route('/slack/command', methods=['POST'])
def slack_command():
    # —— inject admin command execution task
    form = request.form.to_dict()
    admin_mgr.handle_network_execution({
        "execution_id": f"cmd_{int(time.time())}",
        "caller_info": {
            "function_name": "slack_command",
            "user": form.get("user_name"),
            "command_type": form.get("text", "").split()[0] if form.get("text") else "",
            "raw_text": form.get("text")
        },
        "captured_variables": {"form": form}
    })
    # Gloabl status to hold changing status events
    global status
    print(f"Current status: {status}")
    
    print("inside slack command")
    #Gathers the text from the host server form, i.e {text: ':smiley_emoji:'}
    text = request.form.get('text', '')

    # Lowers all text
    gathering_text = text.lower()
    print(gathering_text)

    # Gathers the name of the user who sent the text, i.e {user_id: chrisk}
    user =  request.form.get('user_name')
    #_____________________________________________________________________________________________________________________________________________

    # Prints log for error checking
    print(f"gathering_text: '{gathering_text}'") 

    # Default return to the slack workspace
    response_to_slack = f"{user} sent {gathering_text} to the pixel display - enter '-help' or '-h' for command list"

    # Background processing as wait times for executions would timeout the slack workspace
    if(status != State.OFF):
        # Only processes if screen isn't off
        def background_processing():
            try:
                    get_emoji_url(gathering_text)
                    start_up_file.send_image_to_display(gathering_text)
                    print(f"Successfully processed {gathering_text}")
            except Exception as e:
                    print(f"Error processing {gathering_text}: {e}")
            
        # Start background thread for image displaying
        thread = threading.Thread(target=background_processing)
        thread.daemon = True
        thread.start()

    # For commands that are multi input, are splits and viewed individually i.e 'coffee 5' or 'cancel timer'
    split_input = gathering_text.split()

    if len(split_input) > 1:
        emoji_input = split_input[0]
        emoji_input1 = split_input[1]

        if status != State.TIMER and (emoji_input == 'timer') and status != State.OFF:

            # Casting second input as int for time countdown
            coffeeTime = int(emoji_input1)
            if emoji_input1.isdigit():     
                    
                # Set timer method called in the if len loop as it takes in the second input of emoji_input1
                def set_timer_background():
                    global status
                    try:
                        print(f"Timer set for {coffeeTime} minutes")
                        
                        # Run the function from start_up_file
                        start_up_file.set_timer(emoji_input1)
                        status = State.TIMER
                    except Exception as e:
                        print(f"Error setting timer: {e}")
                        status = State.ON 
                
                # Threads executing the call so it doesnt block timing executions
                thread = threading.Thread(target=set_timer_background)
                thread.daemon = True
                thread.start()

                return f"{user}: set timer for {coffeeTime} minutes, to cancel the timer type (/emoji cancel timer)", 200
            
            # Response if input is not valid for coffee timer
            else:
                return f"{user}: Please provide a valid number of minutes for the coffee timer", 200
        
        # Cancels the timer based on input response from user
        elif status == State.TIMER and gathering_text == 'cancel timer':
            def cancel_timer_background():
                try:
                    mac_add = start_up_file.get_mac_address()
                    off_timer = f"python .\\app.py --address {mac_add} --countdown 0"

                    #Runs the command to turn off the timer
                    result = subprocess.run(off_timer, shell=True, check=True, capture_output=True, text=True)
                    print("Timer cancelled successfully")
                    status = State.ON
                except subprocess.CalledProcessError as e:
                    print(f"Failed to turn off timer: {e}")
            
            # Cancel the timer in background
            cancel_thread = threading.Thread(target=cancel_timer_background)
            cancel_thread.daemon = True
            cancel_thread.start()
            
            # Return immediate response to Slack
            return f"{user}: timer cancelled", 200
            
    #Checks if the text equals to the sleep command, if true, then it sleeps the workspace and deactivates any further prompts to the pixel display
    if (gathering_text == 'sleep') and status != State.OFF:
        def sleep_pixel_display():
            global status 
            try:
                print("screen off successfully")
                start_up_file.turn_screen_off()
                status = State.OFF
            except subprocess.CalledProcessError as e:
                print(f"screen of failed: {e}")

        # Runs screen off thread
        off_thread = threading.Thread(target=sleep_pixel_display)
        off_thread.daemon = True
        off_thread.start()

        return "the pixel display is sleeping, to reactivate enter: /emoji awake"

    # Only if the screen is off can this function call trigger
    if status == State.OFF:
        # Turns the screen back on and reinstates further image processing to the pixel display
        if gathering_text == 'awake':
            def awaken_pixel_display():
                global status 
                try:
                    start_up_file.turn_screen_on()
                    print("screen on succesful")
                    status = State.ON
                except subprocess.CalledProcessError as e:
                    print(f"screen of failed: {e}")
        
            # Runs screen on thread
            on_thread = threading.Thread(target=awaken_pixel_display)
            on_thread.daemon = True
            on_thread.start()

            return f"{user}: pixel display is now awake!", 200
    
    # status update check for if the pixel display is connected
    if gathering_text == 'status':
        status_update = start_up_file.check_if_connected()
        return status_update
       
    # prompts a help screen with guide feature commands
    if gathering_text == '-h'or gathering_text == '-help':
        help_list = start_up_file.command_list() 
        return help_list
       
    return response_to_slack

 
# Uses emoji name codepoint to find corresponding emoji png file name in the twemoji assets, returns this to the get_emoji_url method
def get_standard_emoji_url(emoji_char):
    codepoints = '-'.join(f"{ord(char):x}" for char in emoji_char)
    return f"https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/{codepoints}.png"


#Main execution of program
if __name__ == "__main__":
    # These files trigger upon entry into the flask app for the setup of the IDotMatrix controller sync
    start_up_file.start_up()
    start_up_file.find_mac_address()
    start_up_file.set_mac_address()
    app.run(debug=False, port=8888) 