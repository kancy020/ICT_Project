import requests
import os
import send
    

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


#if __name__ == "__main__":
    # response_emoji = send_emoji("smile")
    # print("Emoji response:", response_emoji)

    # response_welcome = default_welcome_sign()
    # print("Welcome response:", response_welcome)




