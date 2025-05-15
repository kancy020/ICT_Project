import requests
import os

print("send.py started...")

raspPi = "http://192.168.68.110:5000"

def send_emoji(emoji):
    payload = {"emoji": emoji}
    try:
        response = requests.post(raspPi, json=payload)
        response.raise_for_status()
        print("Emoji response:", response.json())
    except Exception as e:
        print("Error sending emoji:", e)

def default_welcome_sign():
    payload = {"text": "Welcome"}
    try:
        response = requests.post(raspPi, json=payload)
        response.raise_for_status()
        print("Welcome response:", response.json())
    except Exception as e:
        print("Error sending welcome:", e)

def slack_alert(message):
    payload = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            }
        ]
    }
    try:
        requests.post(os.environ["SLACK_WEBHOOK_URL"], json=payload)
    except Exception as e:
        print("Error sending Slack alert:", e)

if __name__ == "__main__":
    send_emoji("smile")
    default_welcome_sign()





