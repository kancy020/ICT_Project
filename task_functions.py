import time
from pixel_adapter import pi_adapter 

def show_emoji(emoji: str, **kwargs):
    #表情包
    pi_adapter.show_emoji(emoji, **kwargs)

def show_text(text: str, **kwargs):
    #单词 
    pi_adapter.show_text(text, **kwargs)

def show_GIF(GIF: str,**kwargs):
    #GIF动图
    print("Show GIF display")
    time.sleep(1.5)

def turn_off(**kwargs):
    #关闭
    print("Turning off display")
    time.sleep(1)

def turn_on(**kwargs):
    #开启
    print("Turning on display")
    time.sleep(1)

def sync_time(**kwargs):
    #时钟
    print("Syncing time")
    time.sleep(1)
