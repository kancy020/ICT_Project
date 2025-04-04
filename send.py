import requests

#raspPi = put in raspberry pi IP <-- delete up to equals sign, remove the comment and place the raspPi ip after the equals symbol #  #here 

raspPi = "http://192.168.68.110:5000"

def send_emoji(emoji):
    payload = {"emoji": emoji}
    response = requests.post(raspPi, json=payload)
    return response.json()

def default_welcome_sign():
    payload = {"text": "Welcome"}
    response = requests.post(raspPi, json=payload)
    return response.json()



