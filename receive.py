import os
from flask import Flask, request, Response, jsonify
import logging

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
    gatheringText = request.form.get('text', '')
    user =  request.form.get('user_name')
    print(f"text received from slash command {gatheringText}")
    return f"{user}: sent {gatheringText} to the pixel display ", 200


@app.route('/', methods=['GET'])
def test():
    return Response('It works!'), 200


if __name__ == "__main__":
    app.run(debug=True, port=8888) 