import threading
import time
import requests
from slack_sdk import WebClient

class HeartbeatMonitor:
    def __init__(self, check_url: str, slack_client: WebClient, channel: str):
        self.check_url = check_url
        self.slack = slack_client
        self.channel = channel
        self._running = False
        self.thread = threading.Thread(target=self._monitor)

    def start(self):
        #Start the heartbeat monitoring thread
        self._running = True
        self.thread.start()

    def _monitor(self):
        while self._running:
            try:
                response = requests.get(self.check_url, timeout=5)
                if response.status_code != 200:
                    self._send_alert("Device is offline!")
            except Exception as e:
                self._send_alert(f"Monitoring failed: {str(e)}")
            time.sleep(60)

    def _send_alert(self, message: str):
        #Send a Slack notification
        self.slack.chat_postMessage(channel=self.channel, text=message)

    def simulate_recovery(self):
        #Simulate a recovery notification
        self.slack.chat_postMessage(channel=self.channel, text="Device has reconnected")

class ConnectivityTester:
    @staticmethod
    def test_offline_scenario(monitor: HeartbeatMonitor):
        #Simulate offline scenario
        print("Simulating device offline...")
        monitor._send_alert("[Test] Device offline notification")
    
    @staticmethod
    def test_recovery_scenario(monitor: HeartbeatMonitor):
        #Simulate recovery scenario
        print("Simulating device recovery...")
        monitor.simulate_recovery()
