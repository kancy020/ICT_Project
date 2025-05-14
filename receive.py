import os
from flask import Flask, request, Response, jsonify
import threading
import time
import send
import subprocess

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


status = State.ON



"""
if there is a running thread of timer
check if the user enters the correct keywoard to cancel the timer

if they dont, let the timer continue

if they do, cancel the timer
"""
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
    #Gathers the text from the form, i.e {text: 'smiley_emoji'}
    gathering_text = request.form.get('text', '')
    #Gathers the name of the user who sent the text, i.e {user_id: chrisk}
    user =  request.form.get('user_name')

    #prints log for error checking
    print(f"gathering_text: '{gathering_text}'") 

    #Slpits the text for feature use as some feature require multiple inputs
    split_input = gathering_text.split()

    #If statement that checks if the input it larger than 1 word long, if it is, it splits the words up into two words       
    if len(split_input) > 1:
        emoji_input = split_input[0]
        emoji_input1 = split_input[1]

        #Checks if the first word is coffee, if it is check the second word for a digit for timer input
        if status != State.TIMER:
            if emoji_input == 'coffee'or ':coffee:':
                strToNum = int(emoji_input1)
                if emoji_input1.isdigit():
                    #Chnages status to timer to indiciate that the state of the system is running a timer
                    status = State.TIMER
                    #Seperates time into thread execution
                    timer = threading.Thread(target=coffee_timer, args=(strToNum,))
                    timer.start()
                    status = State.TIMER
                    return f"{user}: set timer for {strToNum} minutes, to cancel the timer type (cancel timer) ", 200
                
        if status == State.TIMER:
             if gathering_text == 'cancel timer':
                status = State.ON
                return "timer is cancelled"
             else:
                return "type (cancel timer) to cancel timer"
 
            

    #Checks if the text equals to the sleep command, if it is, it sleeps the workspace and deactivate any further prompts to the pixel display
    #Until the key word of 'Awaken' is triggered for continuation of commands
    if gathering_text == 'sleep' or gathering_text == ':sleeping_face:':
        status = State.OFF
        return "The pixel display is sleeping, to reactivate enter: awaken"

    if status == State.OFF:
        if gathering_text == 'awaken':
            status = State.ON
            return "Pixel display is now active"
        return "The pixel display is sleeping, to reactivate enter: awaken"
 
    #Generic response to the slack application displaying what the user command was
    if (gathering_text):
            print(f"{user}: sent {gathering_text} to the pixel display")
            return f"{user}: sent {gathering_text} to the pixel display"
    else:
        return "No text"
    
#Coffee timer with default set time of 5 minutes
def coffee_timer(minutes = 5 ):
        #The following code creates a realistic countdown timer using divod functions and specific format layouts
        seconds = minutes * 60
        while seconds:
            mins,secs = divmod(seconds, 60)
            timeformat = f'\r{mins:02d}:{secs:02d}'
            print(timeformat, end='', flush=True)
            time.sleep(1)
            seconds -= 1

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

#Test for connectivity of route
@app.route('/', methods=['GET'])
def test():
    return Response('It works!'), 200

#Main execution of program
if __name__ == "__main__":
    #send the welcome sign on startup
    #send.default_welcome_sign()
    #threading.Thread(target=check_if_online, daemon=True).start()
    app.run(debug=True, port=8888) 