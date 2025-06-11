import re
from abc import ABC, abstractmethod

class ICommandParser(ABC):
    @abstractmethod
    def parse(self, text):
        pass

class SlackCommandParser(ICommandParser):
    def __init__(self):
        self.emoji_map = {
            ":smile:": "😊", ":laugh:": "😂", ":party:": "🎉",
            ":balloon:": "🎈", ":art:": "🎨", ":clock:": "⏰"
        }
        self.commands = {
            "show": "show_emoji",
            "turn off": "turn_off",
            "turn on": "turn_on",
            "flip": "flip",
            "sync": "sync_time"
        }

    def parse(self, text):
        for slack_emoji, unicode_emoji in self.emoji_map.items():
            text = text.replace(slack_emoji, unicode_emoji)
        
        delay = 0
        delay_match = re.search(r"in (\d+)s", text)
        if delay_match:
            delay = int(delay_match.group(1))
            text = text.replace(delay_match.group(0), "")

        emoji = None
        emoji_match = re.search(r"[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF]", text)
        if emoji_match:
            emoji = emoji_match.group()

        command = None
        for cmd_key, cmd_value in self.commands.items():
            if cmd_key in text.lower():
                command = cmd_value
                break

        return {
            "command": command,
            "emoji": emoji,
            "delay": delay,
            "text": text
        }
