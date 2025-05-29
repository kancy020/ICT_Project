import subprocess
import os

class Commands:
    @staticmethod
    def start_up():
        build_path = ("build.ps1")

        subprocess.run([
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", build_path
        ], check=True)

class Main:
    Commands.start_up()
