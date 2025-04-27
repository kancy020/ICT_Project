import requests
import os

print("send.py started...")

# Define the Raspberry Pi server endpoint
raspPi = "http://192.168.68.110:5000"

# Function to send an emoji to the pixel display
def send_emoji(emoji):
    payload = {"emoji": emoji}
    try:
        response = requests.post(raspPi, json=payload)
        response.raise_for_status()
        print("Emoji response:", response.json())
    except Exception as e:
        print("Error sending emoji:", e)

# Function to send a welcome message to the pixel display
def default_welcome_sign():
    payload = {"text": "Welcome"}
    try:
        response = requests.post(raspPi, json=payload)
        response.raise_for_status()
        print("Welcome response:", response.json())
    except Exception as e:
        print("Error sending welcome:", e)

# Function to send a Slack alert message
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

# Main execution for quick testing
if __name__ == "__main__":
    send_emoji("smile")
    default_welcome_sign()



