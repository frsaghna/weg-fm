"""
Interactive Theme Picker Dialog.
Allows choosing themes using j/k, arrow keys, or Enter.
"""

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

from src.theme import THEMES, set_theme, get_current_theme

class ThemePickerWindow(Gtk.Window):
    def __init__(self, parent_win):
        super().__init__(title="Theme Selector")
        self.set_transient_for(parent_win)
        self.set_modal(True)
        self.set_default_size(480, 360)
        self.parent_win = parent_win

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)

        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title = Gtk.Label(label="SELECT THEME", xalign=0.0)
        title.add_css_class("path-label")

        header_box.append(title)
        main_box.append(header_box)
        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # List of Themes
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.connect("row-activated", self._on_row_activated)

        current = get_current_theme()
        selected_row = None

        for key, palette in THEMES.items():
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row_box.set_margin_top(6)
            row_box.set_margin_bottom(6)
            row_box.set_margin_start(10)
            row_box.set_margin_end(10)

            is_active = (key == current)
            prefix = "[x] " if is_active else "[ ] "
            badge = Gtk.Label(label=prefix)
            if is_active:
                badge.add_css_class("selected-checkbox")
            row_box.append(badge)

            lbl_name = Gtk.Label(label=palette['name'], xalign=0.0)
            lbl_name.set_hexpand(True)
            if is_active:
                lbl_name.add_css_class("dir-item")
            else:
                lbl_name.add_css_class("file-item")
            row_box.append(lbl_name)

            cmd_hint = Gtk.Label(label=f":theme {key}", xalign=1.0)
            cmd_hint.add_css_class("key-cap")
            row_box.append(cmd_hint)

            row = Gtk.ListBoxRow()
            row.set_child(row_box)
            row.theme_key = key
            self.list_box.append(row)

            if is_active:
                selected_row = row

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.list_box)
        scrolled.set_vexpand(True)
        main_box.append(scrolled)

        if selected_row:
            self.list_box.select_row(selected_row)

        # Footer
        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        info = Gtk.Label(label="Press Enter to apply, Esc to close", xalign=0.0)
        info.set_hexpand(True)
        info.add_css_class("status-bar")

        close_btn = Gtk.Button(label="Cancel (Esc)")
        close_btn.connect("clicked", lambda b: self.close())

        footer_box.append(info)
        footer_box.append(close_btn)
        main_box.append(footer_box)

        self.set_child(main_box)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

    def _on_row_activated(self, list_box, row):
        if hasattr(row, 'theme_key'):
            ok, msg = set_theme(row.theme_key)
            if self.parent_win and hasattr(self.parent_win, 'update_status'):
                self.parent_win.update_status(msg)
            self.close()

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval in (Gdk.KEY_Escape, Gdk.KEY_q):
            self.close()
            return True
        elif keyval in (Gdk.KEY_j, Gdk.KEY_Down):
            row = self.list_box.get_selected_row()
            idx = row.get_index() if row else 0
            target = self.list_box.get_row_at_index(idx + 1)
            if target:
                self.list_box.select_row(target)
            return True
        elif keyval in (Gdk.KEY_k, Gdk.KEY_Up):
            row = self.list_box.get_selected_row()
            idx = row.get_index() if row else 0
            target = self.list_box.get_row_at_index(max(0, idx - 1))
            if target:
                self.list_box.select_row(target)
            return True
        elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            row = self.list_box.get_selected_row()
            if row:
                self._on_row_activated(self.list_box, row)
            return True
        return False

def show_theme_picker(parent_win):
    win = ThemePickerWindow(parent_win)
    win.present()
