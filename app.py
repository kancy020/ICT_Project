import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

SLACK_TOKEN = os.environ.get("SLACK_TOKEN")
slack_client = WebClient(token=SLACK_TOKEN)

def list_channels():
    """Fetch and print Slack channels"""
    try:
        response = slack_client.conversations_list()
        if response["ok"]:
            return response["channels"]
    except SlackApiError as e:
        print(f"Error retrieving channels: {e.response['error']}")
    return None

def channel_info(channel_id):
    """Fetch channel details"""
    try:
        response = slack_client.conversations_info(channel=channel_id)
        if response["ok"]:
            return response["channel"]
    except SlackApiError as e:
        print(f"Error retrieving channel info: {e.response['error']}")
    return None


if __name__ == '__main__':
    channels = list_channels()
    if channels:
        print("Channels: ")
        for c in channels:
            print(f"{c['name']} ({c['id']})")
            detailed_info = channel_info(c['id'])
            if detailed_info and "latest" in detailed_info:
                print(detailed_info['latest'].get('text', 'No recent messages'))
    else:
        print("Unable to authenticate.")

