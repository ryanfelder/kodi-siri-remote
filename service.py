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
    
    def __init__(self, addon):
        self.addon = addon
        self.debug_enabled = addon.getSetting('debug_enabled') == 'true'
        self.debug_buttons = addon.getSetting('debug_buttons') == 'true'
        
    def log(self, msg, level=xbmc.LOGDEBUG):
        """Log message to Kodi log"""
        xbmc.log(f"[Siri Remote] {msg}", level)
    
    def event_battery(self, percent: int):
        """Battery level event"""
        if self.debug_enabled:
            self.log(f"Battery: {percent}%")
    
    def event_power(self, charging: bool):
        """Power/charging state event"""
        if self.debug_enabled:
            self.log(f"Charging: {charging}")
    
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
            xbmc.executebuiltin('Action(Select)')
            return
        
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
        self.remote = None
        self.listener = None
        self.task = None
        self.loop = None
        
    def log(self, msg, level=xbmc.LOGDEBUG):
        """Log message to Kodi log"""
        xbmc.log(f"[Siri Remote Service] {msg}", level)
    
    def notify(self, msg_id, level=xbmcgui.NOTIFICATION_INFO):
        """Show notification to user"""
        title = self.addon.getLocalizedString(30200)  # "Siri Remote"
        message = self.addon.getLocalizedString(msg_id)
        xbmcgui.Dialog().notification(title, message, level, 3000)
    
    async def connect_remote(self, mac):
        """Connect to the Siri Remote"""
        self.log(f"Connecting to Siri Remote at {mac}...", xbmc.LOGINFO)
        self.log("Note: Device must be paired and trusted in your OS before connecting", xbmc.LOGINFO)
        
        self.listener = KodiRemoteListener(self.addon)
        
        # Create logger function for the remote
        def remote_logger(msg):
            self.log(f"[Remote] {msg}", xbmc.LOGINFO)  # Changed to INFO so we can see it
        
        self.log("Creating SiriRemote instance...", xbmc.LOGINFO)
        self.remote = SiriRemote(mac, self.listener, logger=remote_logger)
        
        self.log("Starting connection...", xbmc.LOGINFO)
        try:
            await self.remote.connect_and_run()
        except KeyboardInterrupt:
            self.log("Connection interrupted", xbmc.LOGINFO)
        except Exception as e:
            error_name = type(e).__name__
            error_msg = str(e)
            
            self.log(f"Remote connection error: {error_name}: {error_msg}", xbmc.LOGERROR)
            
            # Provide helpful messages for common issues
            if "org.bluez.Error" in error_msg or "DBusError" in error_name:
                self.log("", xbmc.LOGERROR)
                self.log("═══════════════════════════════════════════════════════", xbmc.LOGERROR)
                self.log("⚠ BLUETOOTH PAIRING/AUTHORIZATION ERROR", xbmc.LOGERROR)
                self.log("", xbmc.LOGERROR)
                self.log("The Siri Remote must be paired AND trusted before use.", xbmc.LOGERROR)
                self.log("", xbmc.LOGERROR)
                self.log("To fix this, pair your remote using your OS:", xbmc.LOGERROR)
                self.log("  1. Put remote in pairing mode (hold Menu + Volume Up)", xbmc.LOGERROR)
                self.log("  2. Pair via your OS Bluetooth settings", xbmc.LOGERROR)
                self.log("  3. Make sure to TRUST the device after pairing", xbmc.LOGERROR)
                self.log("═══════════════════════════════════════════════════════", xbmc.LOGERROR)
                self.log("", xbmc.LOGERROR)
            elif "CancelledError" in error_name:
                self.log("", xbmc.LOGERROR)
                self.log("═══════════════════════════════════════════════════════", xbmc.LOGERROR)
                self.log("⚠ CONNECTION CANCELLED", xbmc.LOGERROR)
                self.log("", xbmc.LOGERROR)
                self.log("This can happen if the remote is already connected to", xbmc.LOGERROR)
                self.log("BlueZ but not accessible. Try:", xbmc.LOGERROR)
                self.log("  1. Disconnect the remote from Bluetooth settings", xbmc.LOGERROR)
                self.log("  2. Restart the addon", xbmc.LOGERROR)
                self.log("  3. The addon will reconnect automatically", xbmc.LOGERROR)
                self.log("═══════════════════════════════════════════════════════", xbmc.LOGERROR)
                self.log("", xbmc.LOGERROR)
            
            import traceback
            self.log(f"Full traceback:\n{traceback.format_exc()}", xbmc.LOGERROR)
            self.notify(30203, xbmcgui.NOTIFICATION_ERROR)  # "Failed to connect"
            raise
    
    def start(self):
        """Start the service"""
        self.log("Service starting...", xbmc.LOGINFO)
        
        # Check if service is enabled (default to true if not set)
        enabled = self.addon.getSetting('enabled')
        if enabled == 'false':
            self.log("Service is disabled in settings", xbmc.LOGINFO)
            self.notify(30205, xbmcgui.NOTIFICATION_WARNING)  # "Service disabled"
            return
        
        # Get MAC address
        mac_address = self.addon.getSetting('mac_address')
        if not mac_address or mac_address.strip() == '':
            self.log("No MAC address configured", xbmc.LOGWARNING)
            self.notify(30204, xbmcgui.NOTIFICATION_WARNING)  # "No MAC address"
            return
        
        mac_address = mac_address.strip()
        self.log(f"MAC address configured: {mac_address}", xbmc.LOGINFO)
        
        # Start async event loop
        try:
            self.log("Creating asyncio event loop...", xbmc.LOGINFO)
            # Create a new event loop for this thread
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            
            self.log("Event loop created, starting remote connection...", xbmc.LOGINFO)
            # Run the remote connection
            self.notify(30201, xbmcgui.NOTIFICATION_INFO)  # "Connected"
            self.loop.run_until_complete(self.connect_remote(mac_address))
            
            self.log("Event loop completed", xbmc.LOGINFO)
            
        except KeyboardInterrupt:
            self.log("Service interrupted", xbmc.LOGINFO)
        except Exception as e:
            self.log(f"Service error: {type(e).__name__}: {e}", xbmc.LOGERROR)
            import traceback
            self.log(f"Full traceback:\n{traceback.format_exc()}", xbmc.LOGERROR)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources and disconnect from remote"""
        self.log("Cleaning up...", xbmc.LOGINFO)
        
        # Stop the remote
        if self.remote:
            self.log("Stopping remote connection...", xbmc.LOGINFO)
            self.remote.stop()
            
            # Give it a moment to disconnect
            import time
            time.sleep(0.5)
        
        # Close event loop if it exists
        if self.loop and not self.loop.is_closed():
            self.log("Closing event loop...", xbmc.LOGINFO)
            self.loop.close()
        
        self.notify(30202, xbmcgui.NOTIFICATION_INFO)  # "Disconnected"
        self.log("Service stopped and Bluetooth disconnected", xbmc.LOGINFO)


if __name__ == '__main__':
    service = SiriRemoteService()
    service.start()

