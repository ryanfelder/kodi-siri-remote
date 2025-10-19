#!/usr/bin/env python3
"""
Helper script to discover Siri Remote services and characteristics.
Run this to see all available services and their handles/UUIDs.
"""
import asyncio
import sys
from bleak import BleakClient, BleakScanner


async def discover_remote(mac_address):
    """Discover and print all services and characteristics."""
    print(f"Connecting to {mac_address}...")
    
    async with BleakClient(mac_address, timeout=20.0) as client:
        print(f"Connected: {client.is_connected}")
        print(f"MTU Size: {client.mtu_size}")
        print("\n" + "="*80)
        
        for service in client.services:
            print(f"\nService: {service.uuid}")
            print(f"  Description: {service.description}")
            
            for char in service.characteristics:
                print(f"\n  Characteristic: {char.uuid}")
                print(f"    Handle: {char.handle} (0x{char.handle:04x})")
                print(f"    Description: {char.description}")
                print(f"    Properties: {char.properties}")
                
                # Try to read if readable
                if "read" in char.properties:
                    try:
                        value = await client.read_gatt_char(char)
                        print(f"    Current Value: {value.hex()}")
                    except Exception as e:
                        print(f"    (Could not read: {e})")
                
                # Show descriptors
                for desc in char.descriptors:
                    print(f"      Descriptor: {desc.uuid} (handle: {desc.handle})")


async def scan_for_remotes():
    """Scan for nearby Siri Remotes."""
    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover(timeout=5.0)
    
    remotes = []
    print("\nFound devices:")
    for device in devices:
        print(f"  {device.address}: {device.name}")
        if device.address.startswith("48:A9:1C"):
            remotes.append(device)
    
    if remotes:
        print("\nPossible Siri Remotes (MAC starts with 48:A9:1C):")
        for remote in remotes:
            print(f"  {remote.address}: {remote.name}")
    else:
        print("\nNo Siri Remotes found. Make sure it's paired and press a button to wake it.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        mac = sys.argv[1]
        asyncio.run(discover_remote(mac))
    else:
        print("Usage:")
        print("  Discover services: python discover.py <mac-address>")
        print("  Scan for remotes:  python discover.py")
        print("\nAttempting to scan...")
        asyncio.run(scan_for_remotes())

