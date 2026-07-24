"""
Path bar widget supporting breadcrumb display and direct Ctrl+L editing.
"""

import os
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

class PathBarWidget(Gtk.Box):
    def __init__(self, on_navigate):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_margin_start(12)
        self.set_margin_end(12)

        self.on_navigate = on_navigate
        self.current_path = ""
        self.editing = False

        # Path Display Label
        self.path_label = Gtk.Label(label="", xalign=0.0)
        self.path_label.set_hexpand(True)
        self.append(self.path_label)

        # Path Text Entry (hidden by default until Ctrl+L)
        self.path_entry = Gtk.Entry()
        self.path_entry.set_hexpand(True)
        self.path_entry.set_visible(False)
        self.path_entry.connect("activate", self._on_entry_activate)
        
        # Key controller for entry Esc key
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_entry_key_pressed)
        self.path_entry.add_controller(key_ctrl)
        self.append(self.path_entry)

    def set_path(self, path):
        self.current_path = os.path.abspath(path)
        self.path_label.set_text(self.current_path)
        self.path_entry.set_text(self.current_path)
        if self.editing:
            self.stop_editing()

    def start_editing(self):
        self.editing = True
        self.path_entry.set_text(self.current_path)
        self.path_label.set_visible(False)
        self.path_entry.set_visible(True)
        self.path_entry.grab_focus()
        # Select all text in entry for quick replacement
        self.path_entry.select_region(0, -1)

    def stop_editing(self):
        self.editing = False
        self.path_entry.set_visible(False)
        self.path_label.set_visible(True)

    def _on_entry_activate(self, entry):
        new_path = entry.get_text().strip()
        self.stop_editing()
        if new_path and os.path.exists(new_path):
            self.on_navigate(new_path)

    def _on_entry_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.stop_editing()
            return True
        return False
