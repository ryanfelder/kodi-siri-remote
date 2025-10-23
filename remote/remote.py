import asyncio
from dbus_fast.aio import MessageBus
from dbus_fast.constants import BusType
from dbus_fast import Variant


class RemoteListener:
    """Base class for handling remote events"""
    
    def event_battery(self, percent: int):
        pass

    def event_power(self, charging: bool):
        pass

    def event_button(self, button: int):
        pass

    def event_touchpad(self, data):
        pass


class SiriRemote:
    """Siri Remote BLE connection handler using D-Bus directly"""
    
    # UUIDs for GATT characteristics
    _UUID_BATTERY = "00002a19-0000-1000-8000-00805f9b34fb"
    _UUID_POWER = "00002a1a-0000-1000-8000-00805f9b34fb"
    _UUID_HID_INPUT = "00002a4d-0000-1000-8000-00805f9b34fb"
    _UUID_MAGIC_WRITE = "9fbf120d-6301-42d9-8c58-25e699a21dbd"

    _POWER_CHARGING = 171
    _POWER_DISCHARGING = 175
    _POWER_PLUGGED_IN = 187

    BUTTON_RELEASED = 0
    BUTTON_HOME = 1
    BUTTON_VOLUME_UP = 2
    BUTTON_VOLUME_DOWN = 4
    BUTTON_TOUCHPAD = 8
    BUTTON_POWER = 16
    BUTTON_SIRI = 32
    BUTTON_BACK = 64
    BUTTON_MUTE = 128
    BUTTON_PLAY_PAUSE = 256
    BUTTON_UP = 512
    BUTTON_RIGHT = 1024
    BUTTON_DOWN = 2048
    BUTTON_LEFT = 4096

    def __init__(self, mac: str, listener: RemoteListener, logger=None):
        self._mac = mac
        self._listener = listener
        self._bus = None
        self._last_button = 0
        self._running = False
        self._log = logger if logger else print
        self._characteristics = {}

    async def connect_and_run(self):
        """Connect to the remote and run the event loop with auto-reconnect"""
        first_attempt = True
        while True:
            try:
                await self._setup()
            except Exception as e:
                error_type = type(e).__name__
                error_msg = str(e)
                
                # On first attempt, use a longer delay to let system stabilize
                delay = 5 if first_attempt else 2
                
                # Provide helpful error context
                if "Unknown object" in error_msg or "does not exist" in error_msg:
                    self._log(f"Device not found in Bluetooth. Ensure {self._mac} is paired and trusted. Retrying in {delay}s...")
                else:
                    self._log(f"Connection error ({error_type}): {error_msg}")
                    self._log(f"Reconnecting in {delay} seconds...")
                
                self._listener.event_button(0)
                await asyncio.sleep(delay)
                first_attempt = False

    async def _setup(self):
        """Setup connection and enable notifications via D-Bus"""
        self._log(f"Connecting to {self._mac}...")
        
        # Connect to system D-Bus
        self._bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        device_path = f"/org/bluez/hci0/dev_{self._mac.replace(':', '_')}"
        
        try:
            # Get device proxy
            introspection = await self._bus.introspect('org.bluez', device_path)
            device_proxy = self._bus.get_proxy_object('org.bluez', device_path, introspection)
            device_props = device_proxy.get_interface('org.freedesktop.DBus.Properties')
            device_iface = device_proxy.get_interface('org.bluez.Device1')
            
            # Check if connected
            connected = await device_props.call_get('org.bluez.Device1', 'Connected')
            if not connected.value:
                self._log("Connecting to device...")
                await device_iface.call_connect()
                await asyncio.sleep(1)
            
            self._log("Connected")
            
            # Discover GATT services and characteristics
            await self._discover_characteristics(device_path)
            
            # Enable notifications
            await self._enable_notifications()
            
            # Write magic bytes
            await self._write_magic_bytes()
            
            self._log("Ready")
            
            # Keep running
            self._running = True
            while self._running:
                await asyncio.sleep(1)
                
        finally:
            if self._bus:
                self._bus.disconnect()

    async def _discover_characteristics(self, device_path):
        """Discover all GATT characteristics"""
        # Get all managed objects under the device
        om_introspection = await self._bus.introspect('org.bluez', '/')
        om_proxy = self._bus.get_proxy_object('org.bluez', '/', om_introspection)
        om_iface = om_proxy.get_interface('org.freedesktop.DBus.ObjectManager')
        
        objects = await om_iface.call_get_managed_objects()
        
        for obj_path, interfaces in objects.items():
            if not obj_path.startswith(device_path):
                continue
                
            if 'org.bluez.GattCharacteristic1' in interfaces:
                char_props = interfaces['org.bluez.GattCharacteristic1']
                uuid = char_props['UUID'].value.lower()
                handle = char_props.get('Handle')
                handle_val = handle.value if handle else None
                
                # Store characteristic paths
                if uuid == self._UUID_BATTERY.lower():
                    self._characteristics['battery'] = obj_path
                elif uuid == self._UUID_POWER.lower():
                    self._characteristics['power'] = obj_path
                elif uuid == self._UUID_HID_INPUT.lower():
                    # Subscribe to all HID_INPUT - we'll determine type by data
                    key = f'hid_{handle_val}'
                    self._characteristics[key] = obj_path
                elif uuid == self._UUID_MAGIC_WRITE.lower():
                    self._characteristics['magic'] = obj_path

    async def _enable_notifications(self):
        """Enable notifications on characteristics"""
        for name, char_path in self._characteristics.items():
            # Enable notifications for battery, power, and all HID characteristics
            if name in ['battery', 'power'] or name.startswith('hid_'):
                try:
                    introspection = await self._bus.introspect('org.bluez', char_path)
                    char_proxy = self._bus.get_proxy_object('org.bluez', char_path, introspection)
                    char_props = char_proxy.get_interface('org.freedesktop.DBus.Properties')
                    char_iface = char_proxy.get_interface('org.bluez.GattCharacteristic1')
                    
                    # Listen for value changes
                    def make_handler(char_name):
                        def handler(interface, changed, invalidated):
                            if 'Value' in changed:
                                value = bytearray(changed['Value'].value)
                                self._handle_notification(char_name, value)
                        return handler
                    
                    char_props.on_properties_changed(make_handler(name))
                    
                    # Start notify
                    await char_iface.call_start_notify()
                except Exception as e:
                    self._log(f"Warning: Could not enable notifications for {name}")

    async def _write_magic_bytes(self):
        """Write magic bytes to enable input"""
        if 'magic' in self._characteristics:
            try:
                introspection = await self._bus.introspect('org.bluez', self._characteristics['magic'])
                char_proxy = self._bus.get_proxy_object('org.bluez', self._characteristics['magic'], introspection)
                char_iface = char_proxy.get_interface('org.bluez.GattCharacteristic1')
                
                await char_iface.call_write_value([0xF0, 0x00], {'type': Variant('s', 'request')})
            except Exception as e:
                self._log(f"Warning: Could not write magic bytes")

    def _handle_notification(self, char_name, data: bytearray):
        """Handle incoming notification"""
        if char_name == 'battery':
            if len(data) > 0:
                self._listener.event_battery(data[0])
        elif char_name == 'power':
            if len(data) > 0:
                if data[0] == self._POWER_CHARGING:
                    self._listener.event_power(True)
                elif data[0] == self._POWER_DISCHARGING:
                    self._listener.event_power(False)
        elif char_name.startswith('hid_'):
            # Determine type by data length
            if len(data) == 2:
                # Button data
                button = int.from_bytes(data, byteorder='little')
                if button != self._last_button:
                    self._last_button = button
                    self._listener.event_button(button)
            # elif len(data) == 11:
            #     # Touchpad data (disabled - uncomment if needed)
            #     decoded = self._decode_finger(data[4:11])
            #     self._listener.event_touchpad(decoded)

    @staticmethod
    def _decode_finger(data):
        """Decode touchpad finger position data"""
        x = int((data[0] + 255 * (data[1] & 7) - 230) / 15)
        if x < 0:
            x = x + 150
        y = (data[2] if data[2] & 128 else data[2] + 255) - 188
        p = data[5]
        return x, y, p

    def stop(self):
        """Stop the remote event loop"""
        self._running = False
