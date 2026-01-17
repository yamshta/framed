import subprocess
import json
import time

class Simctl:
    @staticmethod
    def list_devices():
        """List all available devices using xcrun simctl list"""
        cmd = ["xcrun", "simctl", "list", "devices", "available", "--json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout)

    @staticmethod
    def boot_device(device_id: str):
        """Boot a device if not already booted"""
        subprocess.run(["xcrun", "simctl", "boot", device_id], check=False)
        # Wait for boot? usually handled by xcodebuild verify, but explicit wait is good
        
    @staticmethod
    def set_status_bar(device_id: str):
        """Override status bar to show 9:41 AM and full battery"""
        cmd = [
            "xcrun", "simctl", "status_bar", device_id, "override",
            "--time", "9:41",
            "--dataNetwork", "wifi",
            "--wifiMode", "active",
            "--wifiBars", "3",
            "--cellularMode", "active",
            "--cellularBars", "4",
            "--batteryState", "charged",
            "--batteryLevel", "100"
        ]
        subprocess.run(cmd, check=True)

    @staticmethod
    def clear_status_bar(device_id: str):
        """Clear status bar override"""
        subprocess.run(["xcrun", "simctl", "status_bar", device_id, "clear"], check=False)

    @staticmethod
    def set_dark_mode(device_id: str, is_dark: bool):
        """Set UI style"""
        style = "dark" if is_dark else "light"
        subprocess.run(["xcrun", "simctl", "ui", device_id, "appearance", style], check=True)
