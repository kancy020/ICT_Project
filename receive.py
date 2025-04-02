import os
from flask import Flask, request, Response, jsonify
import threading
import time
from emoji_list import default_emojis

app = Flask(__name__)

SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")


@app.route('/slack/events', methods=['POST'])
def slack_events():
    payload = request.get_json()

    # Slack URL Verification (needed when enabling event subscriptions)
    if "challenge" in payload:
        return jsonify({"challenge": payload["challenge"]})
    
    return Response(), 200

@app.route('/slack/command', methods=['POST'])
def slack_command():
    gathering_text = request.form.get('text', '')
    user =  request.form.get('user_name')

    print(f"text received from slash command {gathering_text}")

    if (gathering_text):
        return f"{user}: sent {gathering_text} to the pixel display", 200
    
    if (gathering_text not in default_emojis): 
            print("emoji not found. Please try again")
            return "Emoji not found. Please try again", 400
    
    
    if(gathering_text == 'coffee'):
       response_message = f"{user}: set timer for {gathering_text} minutes", 200
       threading.Thread(target=coffee_timer, args=(5,)).start()
       return response_message, 200
    
    

def coffee_timer(minutes = 5 ):
        seconds = minutes * 60
        while seconds:
            mins,secs = divmod(seconds, 60)
            timeformat = f'\r{mins:02d}:{secs:02d}'
            print(timeformat, end='', flush=True)
            time.sleep(1)
            seconds -= 1
    
@app.route('/', methods=['GET'])
def test():
    return Response('It works!'), 200


if __name__ == "__main__":
    #send.default_welcome_sign()
    app.run(debug=True, port=8888) 