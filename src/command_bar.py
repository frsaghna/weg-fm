"""
Command line widget and grammar handler for weg.
Handles prefixes:
  '/' -> Instant local current-dir filter
  '>' -> Recursive search via fd (tiered depth)
  ':' -> Command mode (:new folder, :new file, :rename, :delete, etc.)
"""

import os
import subprocess
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, GLib

class CommandBarWidget(Gtk.Box):
    def __init__(self, on_filter_change, on_search_query, on_command_execute, on_cancel):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.set_margin_top(4)
        self.set_margin_bottom(8)
        self.set_margin_start(12)
        self.set_margin_end(12)

        self.on_filter_change = on_filter_change
        self.on_search_query = on_search_query
        self.on_command_execute = on_command_execute
        self.on_cancel = on_cancel

        self.mode = None # None, '/', '>', ':'

        self.prefix_label = Gtk.Label(label=":")
        self.entry = Gtk.Entry()
        self.entry.set_hexpand(True)
        self.entry.set_placeholder_text("Press /, >, or : for commands...")

        self.append(self.prefix_label)
        self.append(self.entry)

        self.entry.connect("changed", self._on_changed)
        self.entry.connect("activate", self._on_activate)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.entry.add_controller(key_ctrl)

    def activate_mode(self, prefix):
        self.mode = prefix
        self.prefix_label.set_text(prefix)
        self.entry.set_text("")
        self.entry.grab_focus()

    def deactivate(self):
        self.mode = None
        self.prefix_label.set_text(":")
        self.entry.set_text("")
        self.entry.set_placeholder_text("Press /, >, or : for commands...")
        if self.on_cancel:
            self.on_cancel()

    def _on_changed(self, entry):
        text = entry.get_text()
        if self.mode == '/':
            self.on_filter_change(text)
        elif self.mode == '>':
            if len(text) >= 1:
                self.on_search_query(text)

    def _on_activate(self, entry):
        text = entry.get_text().strip()
        if self.mode == ':':
            if text:
                self.on_command_execute(text)
            self.deactivate()
        elif self.mode in ('/', '>'):
            # Keep filter/search active, return focus to list
            if self.on_cancel:
                self.on_cancel(keep_filter=True)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.deactivate()
            return True
        return False
