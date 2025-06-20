import asyncio
from bleak import BleakClient

# MAC address of your Pixel Display Bluetooth device
address = "C4:C4:9C:F5:F4:D8"

# UUID of the writable GATT characteristic on the Pixel Display
UUID = "0000fa02-0000-1000-8000-00805f9b34fb"

async def send_data():
    # Ask the user to input a message to send
    message = input("Please enter the content to send to the Pixel Display (e.g., smile, hello, etc.): ")

    # Connect to the BLE device
    async with BleakClient(address) as client:
        if client.is_connected:
            print("Connected to the Pixel Display device!")
            # Send the message string as bytes via BLE
            await client.write_gatt_char(UUID, message.encode())
            print(f"Sent '{message}' to the Pixel Display!")

# Program entry point: starts the asyncio event loop
asyncio.run(send_data())
