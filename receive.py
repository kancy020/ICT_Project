import os
from flask import Flask, request, Response, jsonify
import requests
import emoji
import subprocess
from datetime import datetime
import json
from task_functions import show_emoji
import Zhuanhuan
from slack_sdk import WebClient
import start_up_file
import threading

app = Flask(__name__)


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

status = State.ON
cancel_event = threading.Event()
timer_thread = None

# Print log with timestamp
def print_log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# Log emoji usage to a file
def log_emoji(emoji):
    log_entry = {
        "emoji": emoji,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open("emoji_log.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    data.append(log_entry)
    with open("emoji_log.json", "w") as f:
        json.dump(data, f, indent=2)

# Test endpoint
@app.route('/', methods=['GET'])
def test():
    return Response('It works!'), 200

# Receive emoji or text via POST
@app.route('/', methods=['POST'])
def receive_emoji():
    data = request.get_json()
    emoji = data.get("emoji")
    text = data.get("text")

    if emoji:
        print_log(f"Received emoji: {emoji}")
        show_emoji(emoji)
        log_emoji(emoji)
        return jsonify({"status": "emoji received", "emoji": emoji}), 200
    elif text:
        print_log(f"Received text: {text}")
        show_emoji(text)
        return jsonify({"status": "text received", "text": text}), 200
    else:
        return jsonify({"error": "No content provided"}), 400

# Slack URL verification
@app.route('/slack/events', methods=['POST'])
def slack_events():
    payload = request.get_json()
    if "challenge" in payload:
        return jsonify({"challenge": payload["challenge"]})
    return Response(), 200

# Handle Slack slash command
@app.route('/slack/command', methods=['POST'])
def slack_command():
    global status, timer_thread

    gathering_text = request.form.get('text', '')
    user = request.form.get('user_name')
    print_log(f"Command from {user}: '{gathering_text}'")

    split_input = gathering_text.split()

    if len(split_input) > 1:
        emoji_input, emoji_input1 = split_input[0], split_input[1]

        if status != State.TIMER:
            if emoji_input in ['coffee', ':coffee:'] and emoji_input1.isdigit():
                minutes = int(emoji_input1)
                status = State.TIMER
                cancel_event.clear()
                timer_thread = threading.Thread(target=coffee_timer, args=(minutes,))
                timer_thread.start()
                return f"{user}: set timer for {minutes} minutes, to cancel type 'cancel timer'", 200

        if status == State.TIMER:
            if gathering_text == 'cancel timer':
                cancel_event.set()
                if timer_thread:
                    timer_thread.join()
                status = State.ON
                return "Timer cancelled.", 200
            return "Timer is running. Type 'cancel timer' to cancel.", 200

    if gathering_text in ['sleep', ':sleeping_face:']:
        status = State.OFF
        return "The pixel display is sleeping. Type 'awaken' to reactivate."

    if status == State.OFF and gathering_text == 'awaken':
        status = State.ON
        return "Pixel display is now active."

    if status == State.OFF:
        return "The pixel display is sleeping. Type 'awaken' to reactivate."

    if gathering_text:
        print_log(f"{user}: sent {gathering_text} to the pixel display")
        show_emoji(gathering_text)
        log_emoji(gathering_text)
        return f"{user}: sent {gathering_text} to the pixel display"
    else:
        return "No text received"

# Countdown timer with cancel support
def coffee_timer(minutes):
    seconds = minutes * 60
    while seconds:
        if cancel_event.is_set():
            print_log("Timer cancelled.")
            return
        mins, secs = divmod(seconds, 60)
        print(f"\r{mins:02d}:{secs:02d}", end='', flush=True)
        time.sleep(1)
        seconds -= 1
    print_log("Timer completed!")
    send.send_emoji("coffee")

# Check connection to pixel display
def check_if_online():
    while True:
        res = subprocess.call(["ping", "192.168.68.110", "-c1", "-W2", "-q"], stdout=subprocess.DEVNULL)
        if res != 0:
            send.slack_alert("Network connection lost to pixel display")
            while True:
                time.sleep(10)
                res = subprocess.call(["ping", "192.168.68.110", "-c1", "-W2", "-q"], stdout=subprocess.DEVNULL)
                if res == 0:
                    send.slack_alert("Network reconnected to pixel display")
                    break
        time.sleep(10)

# Check connection to Slack
def check_slack_connection():
    while True:
        try:
            response = subprocess.run(["ping", "slack.com", "-c", "1", "-W", "2", "-q"], stdout=subprocess.DEVNULL)
            if response.returncode != 0:
                print_log("Slack disconnected")
                send.send_emoji("x")
            else:
                print_log("Slack connected")
        except Exception as e:
            print_log(f"Error checking Slack: {e}")
            send.send_emoji("x")
        time.sleep(10)

# Start Flask app and background threads
if __name__ == "__main__":
    threading.Thread(target=check_if_online, daemon=True).start()
    threading.Thread(target=check_slack_connection, daemon=True).start()
    app.run(host="0.0.0.0", port=8888, debug=True)

#This POST method houses the main features of the program through the slack command intergration
@app.route('/slack/command', methods=['POST'])
def slack_command():
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
