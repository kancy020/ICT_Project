import time

def show_emoji(emoji: str, device_id: int = 0, **kwargs):
    """供任务队列调用的表情显示"""
    print(f"Displaying emoji: {emoji} on device {device_id}")
    time.sleep(1)

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
