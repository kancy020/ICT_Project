
import requests

#raspPi = put in raspberry pi IP <-- delete up to equals sign, remove the comment and place the raspPi ip after the equals symbol #  #here 

def send_emoji(emoji):
    payload = {"emoji": emoji}
    response = requests.post(raspPi, json=payload)
    return response.json()

def default_welcome_sign():
    payload = {"text": "Welcome"}
    response = requests.post(rasPi, json=payload)
    return response.json()


