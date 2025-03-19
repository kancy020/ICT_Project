import os
from flask import Flask, request, Response, jsonify

app = Flask(__name__)

# Load Slack secrets
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")


@app.route('/slack/events', methods=['POST'])
def slack_events():
    """
    Handles incoming Slack Event Subscriptions.
    """
    payload = request.get_json()

    # Slack URL Verification (needed when enabling event subscriptions)
    if "challenge" in payload:
        return jsonify({"challenge": payload["challenge"]})
    
    return Response(), 200

@app.route('/slack/command', methods=['POST'])
def slack_command():
    return Response(), 200
    # data = request.form
    # return jsonify({"response_type": "ephemeral", "text": f"Received: {data.get('text')}"})

@app.route('/', methods=['GET'])
def test():
    return Response('It works!')


if __name__ == "__main__":
    app.run(debug=True, port=8888) 