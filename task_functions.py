import time

def show_emoji(emoji, **kwargs):
    print(f"Displaying emoji: {emoji}")
    time.sleep(2)

def turn_off(**kwargs):
    print("Turning off display")
    time.sleep(1)

def turn_on(**kwargs):
    print("Turning on display")
    time.sleep(1)

def flip(**kwargs):
    print("Flipping display")
    time.sleep(1.5)

def sync_time(**kwargs):
    print("Syncing time")
    time.sleep(1)
