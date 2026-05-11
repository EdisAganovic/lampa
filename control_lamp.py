import asyncio
import json
import os
from bleak import BleakClient, BleakScanner

# Default UUID for ELK-BLEDOM characters
CHARACTERISTIC_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
CONFIG_FILE = "devices.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"default_address": "BE:69:AF:08:2C:03"} # Fallback to your address

def save_config(address):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"default_address": address}, f, indent=4)

class LampController:
    def __init__(self, address=None):
        self.address = address
        self.client = None

    @staticmethod
    async def scan_for_lamps():
        """Scans for nearby devices that look like ELK-BLEDOM lamps."""
        print("Scanning for devices...")
        devices = await BleakScanner.discover(timeout=5.0)
        found = []
        for d in devices:
            name = d.name if d.name else "Unknown Device"
            # Filter for common ELK names
            if any(x in name.upper() for x in ["ELK", "BLEDOM", "MELK", "LED"]):
                found.append({"address": d.address, "name": name})
        return found

    async def connect(self):
        if not self.address:
            return False
        
        # Recreate client to avoid state issues
        self.client = BleakClient(self.address)
        try:
            print(f"Connecting to {self.address}...")
            await self.client.connect()
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()

    async def send_command(self, hex_data, response=True):
        if not self.client or not self.client.is_connected:
            return

        try:
            data = bytes.fromhex(hex_data.replace(" ", ""))
            if len(data) < 9:
                data = data + b"\x00" * (9 - len(data))
            
            # Log for debugging
            # print(f">>> SENDING: {data.hex(' ')}")
            await self.client.write_gatt_char(CHARACTERISTIC_UUID, data, response=response)
        except Exception as e:
            print(f"❌ Command failed: {e}")

    async def power_on(self):
        await self.send_command("7e 04 04 f0 00 01 ff 00 ef")

    async def power_off(self):
        await self.send_command("7e 04 04 00 00 00 ff 00 ef")

    async def set_color(self, r, g, b, response=True):
        hex_cmd = f"7e 00 05 03 {r:02x} {g:02x} {b:02x} 00 ef"
        await self.send_command(hex_cmd, response=response)

    async def set_brightness(self, level, response=True):
        val = int(max(0, min(100, level)))
        hex_cmd = f"7e 04 01 {val:02x} 01 ff ff 00 ef"
        await self.send_command(hex_cmd, response=response)

    async def set_mode(self, mode_id, speed=50, response=True):
        hex_cmd = f"7e 05 03 {mode_id:02x} 06 ff ff 00 ef"
        await self.send_command(hex_cmd, response=response)
        await asyncio.sleep(0.05)
        await self.set_speed(speed, response=response)

    async def set_speed(self, speed, response=True):
        speed_byte = int(max(0, min(100, speed)))
        hex_cmd = f"7e 04 02 {speed_byte:02x} ff ff ff 00 ef"
        await self.send_command(hex_cmd, response=response)
