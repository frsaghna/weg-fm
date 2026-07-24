"""
Path bar widget supporting breadcrumb display, direct Ctrl+L editing,
and top-right nnn-style context/tab indicator (1-8).
"""

import os
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

class PathBarWidget(Gtk.Box):
    def __init__(self, on_navigate, on_context_click=None):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.add_css_class("path-bar")
        self.set_margin_top(0)
        self.set_margin_bottom(0)
        self.set_margin_start(0)
        self.set_margin_end(0)

        self.on_navigate = on_navigate
        self.on_context_click = on_context_click
        self.current_path = ""
        self.editing = False

        # Left: Path Display Label
        self.path_label = Gtk.Label(label="", xalign=0.0)
        self.path_label.add_css_class("path-label")
        self.path_label.set_hexpand(True)
        self.append(self.path_label)

        # Path Text Entry (hidden by default until Ctrl+L)
        self.path_entry = Gtk.Entry()
        self.path_entry.set_hexpand(True)
        self.path_entry.set_visible(False)
        self.path_entry.connect("activate", self._on_entry_activate)
        
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_entry_key_pressed)
        self.path_entry.add_controller(key_ctrl)
        self.append(self.path_entry)

        # Right: Simple Tight Context Indicator Label e.g. "[1] 2 3 4 5 6 7 8"
        self.context_label = Gtk.Label(label="", xalign=1.0)
        self.context_label.add_css_class("context-indicator")
        
        click_gesture = Gtk.GestureClick()
        click_gesture.connect("pressed", self._on_context_label_clicked)
        self.context_label.add_controller(click_gesture)

        self.append(self.context_label)
        self.update_contexts(active_id=1)

    def _on_context_label_clicked(self, gesture, n_press, x, y):
        width = self.context_label.get_width()
        if width > 0 and self.on_context_click:
            # Calculate rough click position for 1-8
            ratio = max(0.0, min(1.0, x / float(width)))
            target_id = max(1, min(8, int(ratio * 8) + 1))
            self.on_context_click(target_id)

    def update_contexts(self, active_id=1):
        parts = []
        for c_id in range(1, 9):
            if c_id == active_id:
                parts.append(f"[{c_id}]")
            else:
                parts.append(f"{c_id}")
        self.context_label.set_text(" ".join(parts))

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
