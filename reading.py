import re
import time
import requests
from datetime import datetime

# Mapping of natural language instructions to device commands
COMMANDS = {
    "show": "DISPLAY_EMOJI",
    "turn off display": "TURN_OFF_DISPLAY",
    "turn on display": "TURN_ON_DISPLAY",
    "flip display": "FLIP_DISPLAY",
    "sync time": "SYNC_TIME"
}

# Mapping for Slack emoji names to actual emoji symbols (can be extended)
EMOJI_MAP = {
    ":grinning:": "😀", ":joy:": "😂", ":tada:": "🎉", ":heart:": "❤️"
}

# Test instructions (these simulate incoming messages from Slack)
test_instructions = [
    "show :grinning: on display",
    "turn off display",
    "flip display",
    "sync time",
    "turn on display"
    "Give me some fried noodles"
]

def parse_command(message):
    """
    Parses the command, extracting emoji, natural language command, and delay if any.
    """
    # Replace emoji names with actual emoji symbols
    for emoji_name, emoji_symbol in EMOJI_MAP.items():
        message = message.replace(emoji_name, emoji_symbol)

    # Extract any time delay (e.g., "in 10s")
    time_match = re.search(r"in (\d+)s", message)
    delay = int(time_match.group(1)) if time_match else 0

    # Extract emoji (supports Unicode emoji ranges)
    emoji_match = re.findall(r"[\U0001F300-\U0001F5FF\U0001F600-\U0001F64F\U0001F680-\U0001F6FF]", message)
    emoji = emoji_match[0] if emoji_match else None

    # Parse the natural language command
    command = None
    for key in COMMANDS:
        if key in message.lower():
            command = COMMANDS[key]
            break

    return {
        "command": command,
        "emoji": emoji,
        "delay": delay
    }

def execute_command(parsed_command):
    """
    Executes the parsed command.
    """
    command = parsed_command["command"]
    emoji = parsed_command["emoji"]
    delay = parsed_command["delay"]

    if delay > 0:
        print(f"Waiting for {delay} seconds before executing command...")
        time.sleep(delay)

    if command == "DISPLAY_EMOJI" and emoji:
        print(f"Displaying emoji: {emoji}")
        # Here you could send a request to control hardware, e.g.:
        # requests.post("http://raspberrypi.local/display", json={"emoji": emoji})
    elif command == "TURN_OFF_DISPLAY":
        print("Turning off the display.")
    elif command == "TURN_ON_DISPLAY":
        print("Turning on the display.")
    elif command == "FLIP_DISPLAY":
        print("Flipping the display 180°.")
    elif command == "SYNC_TIME":
        # Simulating device time sync and returning current device time
        device_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Synchronizing device time. Current device time: {device_time}")
    else:
        print("Unrecognized command.")

# Test the command parsing and execution
for instruction in test_instructions:
    print(f"Processing command: {instruction}")
    parsed = parse_command(instruction)
    execute_command(parsed)
    print()  # Print a newline for readability
