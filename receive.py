import os
from flask import Flask, request, Response, jsonify
import requests
import emoji
import time
import send
import subprocess
import Zhuanhuan
from slack_sdk import WebClient
import start_up_file
import threading

#Initialising the Flask application
app = Flask(__name__)


#Getting slack signing secret from enviorment
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")


#class to hold enum values of system state
class State():
     ON = 1
     OFF = 2
     SLEEPING = 3
     TIMER = 4


# Initializing the status as ON for app entry
status = State.ON
mac_address = start_up_file.mac_address


# Slack bot token which establishes connection to the slack api's event subscription, needed for obtaining images for custom emojis
SLACK_BOT_TOKEN = " -- app slack auth bot token here -- "
client = WebClient(token=SLACK_BOT_TOKEN)


# Obtains the image from the custom emoji slash command send it to the input file and then when process continues to the output images
def get_emoji_url(emoji_name):
    name_e = emoji_name.replace(":", "")
    
    # Ensure input directory exists
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    # Finding the emoji using get_emoji_url function that adds emoji to input folder
    try:
        emoji_char = emoji.emojize(emoji_name, language="alias")
        if emoji_char != emoji_name:
            url = get_standard_emoji_url(emoji_char)
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # Raises exception for bad status codes
                
                # Adding file to input which adds it as a png
                with open(f"input/{name_e}.png", "wb") as file:
                    file.write(response.content)
                
                # Image is processed as a 16 x 16 pixel png which gets added to output folder
                Zhuanhuan.batch_process_single_file(name_e)
                return url
            except requests.RequestException as e:
                print(f"Failed to download standard emoji: {e}")
    except Exception as e:
        print(f"Standard emoji processing failed: {e}")

    
    # For customer emojis retrieves it from the slack client
    try:
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
    global status
    
    print("inside slack command")
    #Gathers the text from the form, i.e {text: ':smiley_emoji:'}
    gathering_text = request.form.get('text', '')

    #Gathers the name of the user who sent the text, i.e {user_id: chrisk}
    user =  request.form.get('user_name')

    #prints log for error checking
    print(f"gathering_text: '{gathering_text}'") 

    # Default return to the slack workspace
    response_to_slack = f"{user} sent {gathering_text} to the pixel display"

    # Background processing as wait times for executions would timeout the slack workspace
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

        if status != State.TIMER and (emoji_input == 'coffee' or emoji_input ==':coffee:'):

            # Casting second input as int for time countdown
            coffeeTime = int(emoji_input1)
            if emoji_input1.isdigit():     
                    
                # Set timer method called in the if len loop as it takes in the second input of emoji_input1
                def set_timer_background():
                    global status
                    try:
                        print(f"Timer set for {coffeeTime} minutes")
                        status = State.TIMER

                        # Run the function from start_up_file
                        start_up_file.set_timer(emoji_input1)
                    except Exception as e:
                        print(f"Error setting timer: {e}")
                        status = State.ON 
                
                # Threads executing the call so it doesnt block timing executions
                thread = threading.Thread(target=set_timer_background)
                thread.daemon = True
                thread.start()

                return f"{user}: set timer for {coffeeTime} minutes, to cancel the timer type (cancel timer)", 200
            
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
            return f"{user}: Timer cancelled", 200
            
    #Checks if the text equals to the sleep command, if true, then it sleeps the workspace and deactivates any further prompts to the pixel display
    #Until the key word of 'Awaken' is triggered for continuation of commands
    if gathering_text == 'sleep' or gathering_text == ':sleeping_face:':
        status = State.OFF
        return "The pixel display is sleeping, to reactivate enter: awaken"

    if status == State.OFF:
        if gathering_text == 'awaken':
            status = State.ON
            return "Pixel display is now active"
        return "The pixel display is sleeping, to reactivate enter: awaken"
    
    return response_to_slack

 
#Checks if the pixel display is returning a ping, if it doesnt, the status of the device if offline
def check_if_online():
        #A loop to continuously check if the display is offline in the backgorund
        while True:
            #Using subprocessing to the device and awaits for reponse
            res = subprocess.call(["ping", "192.168.68.110", "-c1", "-W2", "-q"])
            #Handling the execution based on result 
            if(res == 0):
                #Sleeps the thread for 10 seconds before checking if offline again
                time.sleep(10)
            else:
                #Returns a reponse to slack if it is disconnected
                send.slack_alert("Network connection has been lost to the pixel display")

                #Retry to see if the pixel display has reconnected
                while True:
                    #Sleep timer 
                    time.sleep(10)
                    #Using subprocessing to the device and awaits for reponse
                    res = subprocess.call(["ping", "192.168.68.110", "-c1", "-W2", "-q"])
                    if(res == 0):
                        #Producing alert to the slack workspace
                        send.slack_alert("Network is now connected to the pixel display")
                        break


# Uses emoji name to find corresponding emoji png file name in the twemoji assets, returns this to the get_emoji_url method
def get_standard_emoji_url(emoji_char):
    codepoints = '-'.join(f"{ord(char):x}" for char in emoji_char)
    return f"https://cdn.jsdelivr.net/gh/twitter/twemoji@latest/assets/72x72/{codepoints}.png"


#Test for connectivity of route
@app.route('/', methods=['GET'])
def test():
    return Response('It works!'), 200

#Main execution of program
if __name__ == "__main__":
    start_up_file.start_up()
    start_up_file.find_mac_address()
    start_up_file.set_mac_address()
    app.run(debug=False, port=8888) 