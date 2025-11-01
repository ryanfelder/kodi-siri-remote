#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Siri Remote Service for Kodi
Main service entry point
"""

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import asyncio
import sys
import os
import json
import time

# Add the addon directory to the path so we can import our modules
addon = xbmcaddon.Addon()
addon_path = xbmcvfs.translatePath(addon.getAddonInfo('path'))
sys.path.append(addon_path)

# Add bundled libraries to path
lib_path = os.path.join(addon_path, 'lib')
if os.path.exists(lib_path):
    sys.path.insert(0, lib_path)

from remote.remote import SiriRemote, RemoteListener


class KodiRemoteListener(RemoteListener):
    """Listener that converts Siri Remote events to Kodi actions"""

    def __init__(self, addon, remote_name="Remote"):
        self.addon = addon
        self.remote_name = remote_name
        self.debug_enabled = addon.getSetting('debug_enabled') == 'true'
        self.debug_buttons = addon.getSetting('debug_buttons') == 'true'
        
    def log(self, msg, level=xbmc.LOGDEBUG):
        """Log message to Kodi log"""
        xbmc.log(f"[Siri Remote - {self.remote_name}] {msg}", level)
    
    def event_battery(self, percent: int):
        """Battery level event"""
        if self.debug_enabled:
            self.log(f"Battery: {percent}%")
    
    def event_power(self, charging: bool):
        """Power/charging state event"""
        if self.debug_enabled:
            self.log(f"Charging: {charging}")
    
    async def inhibit_screensaver(self):
        """Inhibit the screensaver"""
        xbmc.executebuiltin('InhibitScreensaver(True)')
        await asyncio.sleep(0.5)
        xbmc.executebuiltin('InhibitScreensaver(False)')
    
    def event_button(self, button: int):
        """Button press event - convert to Kodi actions"""
        if self.debug_enabled and self.debug_buttons:
            self.log(f"Button event: {button} (0x{button:04x})")
        
        # Handle button release
        if button == SiriRemote.BUTTON_RELEASED:
            if self.debug_enabled and self.debug_buttons:
                self.log("All buttons released")
            return
        
        # Check if screensaver is active - if so, wake it and discard the event
        if xbmc.getCondVisibility('System.ScreenSaverActive'):
            if self.debug_buttons:
                self.log("Screensaver active - waking and discarding button event", xbmc.LOGINFO)
            # Send a simple action to wake the screensaver
            asyncio.create_task(self.inhibit_screensaver())
            return
        else:
            asyncio.create_task(self.inhibit_screensaver())

        # Map buttons to Kodi actions
        # Note: We trigger on press, not release, so each button press executes immediately
        if button & SiriRemote.BUTTON_HOME:
            if self.debug_buttons:
                self.log("HOME button -> ActivateWindow(Home)", xbmc.LOGINFO)
            xbmc.executebuiltin('ActivateWindow(Home)')
        
        if button & SiriRemote.BUTTON_VOLUME_UP:
            if self.debug_buttons:
                self.log("VOLUME_UP button -> Action(VolumeUp)", xbmc.LOGINFO)
            xbmc.executebuiltin('Action(VolumeUp)')
        
        if button & SiriRemote.BUTTON_VOLUME_DOWN:
            if self.debug_buttons:
                self.log("VOLUME_DOWN button -> Action(VolumeDown)", xbmc.LOGINFO)
            xbmc.executebuiltin('Action(VolumeDown)')
        
        if button & SiriRemote.BUTTON_TOUCHPAD:
            # Check if we're in fullscreen video
            fullscreen_video = xbmc.getCondVisibility('Window.IsActive(FullscreenVideo)')
            if fullscreen_video:
                # Check if OSD is visible
                osd_visible = xbmc.getCondVisibility('Window.IsVisible(VideoOSD)')
                if not osd_visible:
                    # OSD not visible, show it
                    if self.debug_buttons:
                        self.log("TOUCHPAD button (fullscreen, no OSD) -> Show OSD", xbmc.LOGINFO)
                    xbmc.executebuiltin('Action(OSD)')
                else:
                    # OSD visible, select
                    if self.debug_buttons:
                        self.log("TOUCHPAD button (OSD visible) -> Select", xbmc.LOGINFO)
                    xbmc.executebuiltin('Action(Select)')
            else:
                # Not in fullscreen video, just select
                if self.debug_buttons:
                    self.log("TOUCHPAD button -> Select", xbmc.LOGINFO)
                xbmc.executebuiltin('Action(Select)')
        
        if button & SiriRemote.BUTTON_POWER:
            if self.debug_buttons:
                self.log("POWER button -> Quit", xbmc.LOGINFO)
            xbmc.executebuiltin('Quit')
        
        if button & SiriRemote.BUTTON_SIRI:
            # Siri button always shows OSD during playback, context menu otherwise
            player = xbmc.Player()
            if player.isPlayingVideo():
                if self.debug_buttons:
                    self.log("SIRI button (playing) -> OSD", xbmc.LOGINFO)
                xbmc.executebuiltin('Action(OSD)')
            else:
                if self.debug_buttons:
                    self.log("SIRI button -> ContextMenu", xbmc.LOGINFO)
                xbmc.executebuiltin('Action(ContextMenu)')
        
        if button & SiriRemote.BUTTON_BACK:
            if self.debug_buttons:
                self.log("BACK button -> Back", xbmc.LOGINFO)
            xbmc.executebuiltin('Action(Back)')
        
        if button & SiriRemote.BUTTON_MUTE:
            if self.debug_buttons:
                self.log("MUTE button -> Mute", xbmc.LOGINFO)
            xbmc.executebuiltin('Mute')
        
        if button & SiriRemote.BUTTON_PLAY_PAUSE:
            # During playback, pause/play. Otherwise show OSD.
            player = xbmc.Player()
            if player.isPlayingVideo():
                if self.debug_buttons:
                    self.log("PLAY_PAUSE button (playing) -> Pause", xbmc.LOGINFO)
                xbmc.executebuiltin('Action(Pause)')
            else:
                if self.debug_buttons:
                    self.log("PLAY_PAUSE button -> Action(PlayPause)", xbmc.LOGINFO)
                xbmc.executebuiltin('Action(PlayPause)')
        
        if button & SiriRemote.BUTTON_UP:
            # Check if we're in fullscreen video
            fullscreen_video = xbmc.getCondVisibility('Window.IsActive(FullscreenVideo)')
            if fullscreen_video:
                # Check if OSD is visible
                osd_visible = xbmc.getCondVisibility('Window.IsVisible(VideoOSD)')
                if not osd_visible:
                    # Show OSD first
                    if self.debug_buttons:
                        self.log("UP button (fullscreen, no OSD) -> BigStepForward", xbmc.LOGINFO)
                    xbmc.executebuiltin('Action(BigStepForward)')
                else:
                    # Navigate in OSD
                    if self.debug_buttons:
                        self.log("UP button (OSD visible) -> Up", xbmc.LOGINFO)
                    xbmc.executebuiltin('Action(Up)')
            else:
                if self.debug_buttons:
                    self.log("UP button -> Up", xbmc.LOGINFO)
                xbmc.executebuiltin('Action(Up)')
        
        if button & SiriRemote.BUTTON_DOWN:
            # Check if we're in fullscreen video
            fullscreen_video = xbmc.getCondVisibility('Window.IsActive(FullscreenVideo)')
            if fullscreen_video:
                # Check if OSD is visible
                osd_visible = xbmc.getCondVisibility('Window.IsVisible(VideoOSD)')
                if not osd_visible:
                    # Show OSD first
                    if self.debug_buttons:
                        self.log("DOWN button (fullscreen, no OSD) -> BigStepBack", xbmc.LOGINFO)
                    xbmc.executebuiltin('Action(BigStepBack)')
                else:
                    # Navigate in OSD
                    if self.debug_buttons:
                        self.log("DOWN button (OSD visible) -> Down", xbmc.LOGINFO)
                    xbmc.executebuiltin('Action(Down)')
            else:
                if self.debug_buttons:
                    self.log("DOWN button -> Down", xbmc.LOGINFO)
                xbmc.executebuiltin('Action(Down)')
        
        if button & SiriRemote.BUTTON_LEFT:
            # Check if we're in fullscreen video
            fullscreen_video = xbmc.getCondVisibility('Window.IsActive(FullscreenVideo)')
            if fullscreen_video:
                # Check if OSD is visible
                osd_visible = xbmc.getCondVisibility('Window.IsVisible(VideoOSD)')
                if not osd_visible:
                    # Skip backward when OSD not visible
                    if self.debug_buttons:
                        self.log("LEFT button (fullscreen, no OSD) -> StepBack", xbmc.LOGINFO)
                    xbmc.executebuiltin('Action(StepBack)')
                else:
                    # Navigate in OSD
                    if self.debug_buttons:
                        self.log("LEFT button (OSD visible) -> Left", xbmc.LOGINFO)
                    xbmc.executebuiltin('Action(Left)')
            else:
                if self.debug_buttons:
                    self.log("LEFT button -> Left", xbmc.LOGINFO)
                xbmc.executebuiltin('Action(Left)')
        
        if button & SiriRemote.BUTTON_RIGHT:
            # Check if we're in fullscreen video
            fullscreen_video = xbmc.getCondVisibility('Window.IsActive(FullscreenVideo)')
            if fullscreen_video:
                # Check if OSD is visible
                osd_visible = xbmc.getCondVisibility('Window.IsVisible(VideoOSD)')
                if not osd_visible:
                    # Skip forward when OSD not visible
                    if self.debug_buttons:
                        self.log("RIGHT button (fullscreen, no OSD) -> StepForward", xbmc.LOGINFO)
                    xbmc.executebuiltin('Action(StepForward)')
                else:
                    # Navigate in OSD
                    if self.debug_buttons:
                        self.log("RIGHT button (OSD visible) -> Right", xbmc.LOGINFO)
                    xbmc.executebuiltin('Action(Right)')
            else:
                if self.debug_buttons:
                    self.log("RIGHT button -> Right", xbmc.LOGINFO)
                xbmc.executebuiltin('Action(Right)')
    
    def event_touchpad(self, data):
        """Touchpad event - currently not used"""
        if self.debug_enabled:
            self.log(f"Touchpad: x={data[0]}, y={data[1]}, pressure={data[2]}")


class SiriRemoteService:
    """Main service class"""
    
    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.monitor = xbmc.Monitor()
        self.remotes = []  # List of remote instances
        self.tasks = []    # List of async tasks
        self.loop = None
        
    def log(self, msg, level=xbmc.LOGDEBUG):
        """Log message to Kodi log"""
        xbmc.log(f"[Siri Remote Service] {msg}", level)
    
    def notify(self, msg_id, level=xbmcgui.NOTIFICATION_INFO):
        """Show notification to user"""
        title = self.addon.getLocalizedString(30200)  # "Siri Remote"
        message = self.addon.getLocalizedString(msg_id)
        xbmcgui.Dialog().notification(title, message, level, 3000)
    
    async def connect_remote(self, remote_name, mac):
        """Connect to a single Siri Remote and handle reconnections
        
        Args:
            remote_name: Display name for the remote
            mac: MAC address of the remote
        """
        self.log(f"Starting connection handler for {remote_name} ({mac})...", xbmc.LOGINFO)
        
        listener = KodiRemoteListener(self.addon, remote_name)
        
        # Create logger function for the remote
        # Always log important messages, but filter verbose debug messages
        debug_enabled = self.addon.getSetting('debug_enabled') == 'true'
        def remote_logger(msg):
            # Always log connection status, errors, and important messages
            important_keywords = ['Connecting', 'Connected', 'disconnected', 'error', 'Error', 
                                  'failed', 'Failed', 'Waiting', 'ready', 'Warning']
            is_important = any(keyword in msg for keyword in important_keywords)
            
            if debug_enabled or is_important:
                self.log(f"[{remote_name}] {msg}", xbmc.LOGINFO)
        
        remote = SiriRemote(mac, listener, logger=remote_logger)
        self.remotes.append(remote)
        
        try:
            await remote.connect_and_run()
        except KeyboardInterrupt:
            self.log(f"{remote_name}: Connection interrupted", xbmc.LOGINFO)
        except Exception as e:
            error_msg = str(e)
            
            # Provide helpful messages for common issues
            if "org.bluez.Error" in error_msg or "DBusError" in type(e).__name__:
                self.log(f"{remote_name}: Bluetooth connection failed. Please ensure your Siri Remote is paired and trusted in your OS Bluetooth settings.", xbmc.LOGERROR)
            elif "CancelledError" in type(e).__name__:
                self.log(f"{remote_name}: Connection was cancelled. Try disconnecting the remote from Bluetooth settings and restart the addon.", xbmc.LOGERROR)
            else:
                self.log(f"{remote_name}: Remote connection error: {error_msg}", xbmc.LOGERROR)
            
            # Show detailed traceback only if debug is enabled
            debug_enabled = self.addon.getSetting('debug_enabled') == 'true'
            if debug_enabled:
                import traceback
                self.log(f"{remote_name} Traceback:\n{traceback.format_exc()}", xbmc.LOGERROR)
    
    async def run_all_remotes(self, remotes):
        """Run connection tasks for all configured remotes concurrently
        
        Args:
            remotes: List of tuples (name, mac_address) for enabled remotes
        """
        if not remotes:
            self.log("No remotes to connect", xbmc.LOGWARNING)
            return
        
        self.log(f"Starting monitoring for {len(remotes)} remote(s)...", xbmc.LOGINFO)
        self.log("Remotes will auto-connect when they wake up from sleep", xbmc.LOGINFO)
        
        # Create tasks for all remotes with staggered start
        # Brief delay between remotes to avoid overwhelming D-Bus
        tasks = []
        for idx, (remote_name, mac) in enumerate(remotes):
            # Small stagger to avoid D-Bus contention
            if idx > 0:
                await asyncio.sleep(1)
            
            task = asyncio.create_task(self.connect_remote(remote_name, mac))
            tasks.append(task)
            self.tasks.append(task)
        
        # Wait for all tasks (they run indefinitely with auto-reconnect)
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except KeyboardInterrupt:
            self.log("All remote connections interrupted", xbmc.LOGINFO)
        except Exception as e:
            self.log(f"Error in remote connection handler: {e}", xbmc.LOGERROR)
    
    def _migrate_old_settings(self):
        """Migrate old single-remote settings to new multi-remote format"""
        old_enabled = self.addon.getSetting('enabled')
        old_mac = self.addon.getSetting('mac_address')
        
        # If old settings exist and remote1 is not configured, migrate
        if old_mac and old_mac.strip() != '':
            remote1_mac = self.addon.getSetting('remote1_mac')
            if not remote1_mac or remote1_mac.strip() == '':
                self.log("Migrating old settings to new multi-remote format", xbmc.LOGINFO)
                self.addon.setSetting('remote1_mac', old_mac.strip())
                self.addon.setSetting('remote1_enabled', old_enabled if old_enabled else 'true')
                self.addon.setSetting('remote1_name', 'Remote 1')
    
    def _get_configured_remotes(self):
        """Get list of configured and enabled remotes
        
        Returns:
            list: List of tuples (name, mac_address) for enabled remotes
        """
        remotes = []
        for i in range(1, 5):  # Support up to 4 remotes
            enabled = self.addon.getSetting(f'remote{i}_enabled')
            mac = self.addon.getSetting(f'remote{i}_mac')
            name = self.addon.getSetting(f'remote{i}_name')
            
            if enabled == 'true' and mac and mac.strip() != '':
                remote_name = name if name and name.strip() != '' else f'Remote {i}'
                remotes.append((remote_name, mac.strip()))
        
        return remotes
    
    async def _wait_for_bluetooth(self, max_wait=30):
        """Wait for Bluetooth D-Bus service to be ready
        
        Args:
            max_wait: Maximum seconds to wait for Bluetooth service
            
        Returns:
            bool: True if service is ready, False if timeout
        """
        from dbus_fast.aio import MessageBus
        from dbus_fast.constants import BusType
        
        self.log("Waiting for Bluetooth service to be ready...", xbmc.LOGINFO)
        
        for attempt in range(max_wait):
            try:
                # Try to connect to D-Bus and check if bluez is available
                bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
                try:
                    # Try to introspect the bluez root object
                    await bus.introspect('org.bluez', '/')
                    self.log("Bluetooth service is ready", xbmc.LOGINFO)
                    return True
                finally:
                    bus.disconnect()
            except Exception as e:
                if attempt == 0:
                    self.log(f"Bluetooth not ready yet, waiting... ({e})", xbmc.LOGDEBUG)
                await asyncio.sleep(1)
        
        self.log(f"Bluetooth service not available after {max_wait} seconds", xbmc.LOGERROR)
        return False
    
    def start(self):
        """Start the service"""
        self.log("Service starting...", xbmc.LOGINFO)
        
        # Wait for system to stabilize after boot
        # This helps ensure Bluetooth and D-Bus services are ready
        self.log("Waiting for system initialization...", xbmc.LOGINFO)
        time.sleep(3)
        
        # Migrate old settings if they exist
        self._migrate_old_settings()
        
        # Get configured remotes
        remotes = self._get_configured_remotes()
        
        if not remotes:
            self.log("No remotes configured or enabled", xbmc.LOGWARNING)
            self.notify(30204, xbmcgui.NOTIFICATION_WARNING)  # "No MAC address"
            return
        
        self.log(f"Found {len(remotes)} enabled remote(s)", xbmc.LOGINFO)
        for name, mac in remotes:
            self.log(f"  - {name}: {mac}", xbmc.LOGINFO)
        
        # Start async event loop
        try:
            # Create a new event loop for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            # Wait for Bluetooth service to be ready
            bt_ready = self.loop.run_until_complete(self._wait_for_bluetooth(max_wait=30))
            if not bt_ready:
                self.log("Cannot start: Bluetooth service unavailable", xbmc.LOGERROR)
                self.notify(30203, xbmcgui.NOTIFICATION_ERROR)  # "Failed to connect"
                return
            
            # Run all remote connections concurrently
            # Note: Remotes may not connect immediately if they're asleep
            # They will auto-connect when you press any button on them
            self.log("Remote monitoring active. Remotes will connect when they wake up.", xbmc.LOGINFO)
            self.notify(30201, xbmcgui.NOTIFICATION_INFO)  # "Connected"
            self.loop.run_until_complete(self.run_all_remotes(remotes))
            
        except KeyboardInterrupt:
            self.log("Service interrupted", xbmc.LOGINFO)
        except Exception as e:
            self.log(f"Service error: {e}", xbmc.LOGERROR)
            # Show detailed traceback only if debug is enabled
            debug_enabled = self.addon.getSetting('debug_enabled') == 'true'
            if debug_enabled:
                import traceback
                self.log(f"Traceback:\n{traceback.format_exc()}", xbmc.LOGERROR)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources and disconnect from all remotes"""
        self.log("Cleaning up...", xbmc.LOGINFO)
        
        # Stop all remotes
        for remote in self.remotes:
            try:
                remote.stop()
            except Exception as e:
                self.log(f"Error stopping remote: {e}", xbmc.LOGERROR)
        
        # Give them a moment to disconnect
        if self.remotes:
            import time
            time.sleep(0.5)
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Close event loop if it exists
        if self.loop and not self.loop.is_closed():
            self.loop.close()
        
        self.notify(30202, xbmcgui.NOTIFICATION_INFO)  # "Disconnected"
        self.log("Service stopped", xbmc.LOGINFO)


if __name__ == '__main__':
    service = SiriRemoteService()
    service.start()

