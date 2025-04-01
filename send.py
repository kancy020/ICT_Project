
import requests

#raspPi = put in raspberry pi IP 

def send_emoji(emoji):
    payload = {"emoji": emoji}
    response = requests.post(raspPi, json=payload)
    return response.json()


