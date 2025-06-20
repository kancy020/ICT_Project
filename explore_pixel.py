import os
from bleak import BleakClient
import asyncio

# Load MAC address from environment variable or fallback value
address = os.environ.get("PIXEL_DEVICE_MAC", "00:00:00:00:00:00")

async def explore():
    async with BleakClient(address) as client:
        if client.is_connected:
            print("Connected to Pixel Device!")
            for service in client.services:
                print(f"[Service] {service.uuid}")
                for char in service.characteristics:
                    print(f"  [Characteristic] {char.uuid}: {char.properties}")

asyncio.run(explore())
