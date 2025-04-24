import requests
import os

raspPi = "http://192.168.68.110:5000"

def send_emoji(emoji):
    payload = {"emoji": emoji}
    response = requests.post(raspPi, json=payload)
    return response.json()

def default_welcome_sign():
    payload = {"text": "Welcome"}
    response = requests.post(raspPi, json=payload)
    return response.json()

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
    requests.post(os.environ["SLACK_WEBHOOK_URL"], json=payload) #-- TODO -- create a slack webhook connection


if __name__ == "__main__":
    response_emoji = send_emoji("smile")
    print("Emoji response:", response_emoji)

    response_welcome = default_welcome_sign()
    print("Welcome response:", response_welcome)




