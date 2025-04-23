import requests

raspPi = "http://192.168.68.110:5000"

def send_emoji(emoji):
    payload = {"emoji": emoji}
    response = requests.post(raspPi, json=payload)
    return response.json()

def default_welcome_sign():
    payload = {"text": "Welcome"}
    response = requests.post(raspPi, json=payload)
    return response.json()

if __name__ == "__main__":
    response_emoji = send_emoji("smile")
    print("Emoji response:", response_emoji)

    response_welcome = default_welcome_sign()
    print("Welcome response:", response_welcome)




