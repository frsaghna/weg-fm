"""
Directory monitoring using GIO's GFileMonitor for live updating.
"""

import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib

class DirectoryMonitor:
    def __init__(self, on_change_callback):
        self.on_change_callback = on_change_callback
        self._monitor = None
        self._gfile = None

    def set_directory(self, path):
        if self._monitor:
            self._monitor.cancel()
            self._monitor = None

        self._gfile = Gio.File.new_for_path(path)
        try:
            self._monitor = self._gfile.monitor_directory(
                Gio.FileMonitorFlags.NONE,
                None
            )
            self._monitor.connect("changed", self._on_changed)
        except Exception as e:
            print(f"[DirectoryMonitor] Failed to monitor {path}: {e}")

    def _on_changed(self, monitor, file, other_file, event_type):
        # Trigger directory reload on file changes
        GLib.idle_add(self.on_change_callback)

    def stop(self):
        if self._monitor:
            self._monitor.cancel()
            self._monitor = None
