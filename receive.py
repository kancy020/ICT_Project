import os
import send
import emoji_list
import slack_features
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

emoji_list

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

        return f"{user}: sent {gathering_text} to the pixel display ", 200
    
    while(gathering_text not in emoji_list.default_emojis): {
            print("emoji not found. Please try again")
    }
    
    if(gathering_text == 'coffee'):
        return "Please enter length of time", 200
    
    

    


@app.route('/', methods=['GET'])
def test():
    return Response('It works!'), 200


if __name__ == "__main__":
    #send.default_welcome_sign()
    app.run(debug=True, port=8888) 