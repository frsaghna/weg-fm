"""
Main application window for weg.
Assembles UI widgets and handles keyboard navigation events.
"""

import os
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gdk, Gio, GLib

from src.path_bar import PathBarWidget
from src.file_list import FileListWidget
from src.monitor import DirectoryMonitor

class WegWindow(Gtk.ApplicationWindow):
    def __init__(self, app, initial_dir=None):
        super().__init__(application=app, title="weg")
        self.set_default_size(700, 500)

        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser("~")
        self.current_dir = os.path.abspath(initial_dir)

        # Directory monitor
        self.monitor = DirectoryMonitor(self._on_directory_changed)

        # Layout Container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # 1. Top Path Bar
        self.path_bar = PathBarWidget(on_navigate=self.navigate_to)
        main_box.append(self.path_bar)

        # Separator
        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # 2. Middle File List
        self.file_list = FileListWidget(
            on_open_directory=self.navigate_to,
            on_status_change=self.update_status
        )
        main_box.append(self.file_list)

        # Separator
        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # 3. Status Bar
        self.status_bar = Gtk.Label(label="Ready", xalign=0.0)
        self.status_bar.set_margin_top(4)
        self.status_bar.set_margin_bottom(4)
        self.status_bar.set_margin_start(12)
        self.status_bar.set_margin_end(12)
        main_box.append(self.status_bar)

        # 4. Persistent Command Line (bottom)
        cmd_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cmd_box.set_margin_top(4)
        cmd_box.set_margin_bottom(8)
        cmd_box.set_margin_start(12)
        cmd_box.set_margin_end(12)
        
        self.cmd_prefix_label = Gtk.Label(label=":")
        self.cmd_entry = Gtk.Entry()
        self.cmd_entry.set_hexpand(True)
        self.cmd_entry.set_placeholder_text("Press /, >, or : for commands...")
        
        cmd_box.append(self.cmd_prefix_label)
        cmd_box.append(self.cmd_entry)
        main_box.append(cmd_box)

        self.set_child(main_box)

        # Key Navigation Event Controller
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

        # Initial directory load
        self.navigate_to(self.current_dir)

    def navigate_to(self, path):
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            return

        self.current_dir = path
        self.path_bar.set_path(path)
        self.file_list.load_directory(path)
        self.monitor.set_directory(path)
        self.file_list.grab_focus()

    def update_status(self, text):
        self.status_bar.set_text(text)

    def _on_directory_changed(self):
        # Called when GFileMonitor detects a change in current_dir
        if self.current_dir:
            self.file_list.load_directory(self.current_dir)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        # Ignore global navigation keys if typing in entry widgets
        focus = self.get_focus()
        if focus in (self.path_bar.path_entry, self.cmd_entry):
            return False

        ctrl_pressed = bool(state & Gdk.ModifierType.CONTROL_MASK)

        # Ctrl+L: Edit path directly
        if ctrl_pressed and (keyval in (Gdk.KEY_l, Gdk.KEY_L)):
            self.path_bar.start_editing()
            return True

        # Navigation keys: ↑/k, ↓/j
        if keyval in (Gdk.KEY_Up, Gdk.KEY_k):
            self.file_list.move_selection(-1)
            return True
        elif keyval in (Gdk.KEY_Down, Gdk.KEY_j):
            self.file_list.move_selection(1)
            return True

        # Enter: Open file/dir
        elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.file_list.activate_selected()
            return True

        # Backspace: Parent directory
        elif keyval == Gdk.KEY_BackSpace:
            parent = os.path.dirname(self.current_dir)
            if parent and parent != self.current_dir:
                self.navigate_to(parent)
            return True

        return False
