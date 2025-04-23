import os
from flask import Flask, request, Response, jsonify
import threading
import time
from emoji_list import emoji_list

#Initialising the Flask application
app = Flask(__name__)

#Getting slack signing secret from enviorment
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

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
    if(len(split_input) > 1 ):
        emoji_input = split_input[0]
        emoji_input1 = split_input[1]

        #Checks if the first word is coffee, if it is check the second word for a digit for timer input
        if(emoji_input == 'coffee'or ':coffee:'):
            strToNum = int(emoji_input1)
            if(emoji_input1.isdigit()):
                #Seperates times into seperate thread so other features can execute without disrupting the timer
                threading.Thread(target=coffee_timer, args=(strToNum,)).start()
                return f"{user}: set timer for {strToNum} minutes", 200

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

def offline_message():
     
#Test for connectivity of route
@app.route('/', methods=['GET'])
def test():
    return Response('It works!'), 200

#Main execution of program
if __name__ == "__main__":
    #send the welcome sign on startup
    #send.default_welcome_sign()
    app.run(debug=True, port=8888) 