import os
from flask import Flask, request, Response, jsonify
import threading
import time
from emoji_list import emoji_list

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
    print("inside slack command")
    gathering_text = request.form.get('text', '')
    user =  request.form.get('user_name')

    print(f"gathering_text: '{gathering_text}'") 

    split_input = gathering_text.split()

    if(len(split_input) > 1 ):
        emoji_input = split_input[0]
        emoji_input1 = split_input[1]

        if(emoji_input == 'coffee'or ':coffee:'):
            strToNum = int(emoji_input1)
            if(emoji_input1.isdigit()):
                threading.Thread(target=coffee_timer, args=(strToNum,)).start()
                return f"{user}: set timer for {strToNum} minutes", 200

    if (gathering_text in emoji_list):
            print(f"{user}: sent {gathering_text} to the pixel display")
            return f"{user}: sent {gathering_text} to the pixel display"



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