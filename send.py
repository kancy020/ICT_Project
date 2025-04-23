import requests
import receive

#raspPi = put in raspberry pi IP <-- delete up to equals sign, remove the comment and place the raspPi ip after the equals symbol #  #here 

def send_emoji(emoji):
    payload = {"emoji": emoji}
    response = requests.post(raspPi, json=payload)
    return response.json()

#Displays a welcome text when the raspberryPi starts up slack
def default_welcome_sign():
    payload = {"text": "Welcome"}
    response = requests.post(raspPi, json=payload)
    return response.json()

if __name__ == "__main__":
    response_emoji = send_emoji("smile")
    print("Emoji response:", response_emoji)

    response_welcome = default_welcome_sign()
    print("Welcome response:", response_welcome)




