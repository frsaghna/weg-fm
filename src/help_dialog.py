"""
Structured TUI Help Overlay Dialog for weg.
Renders keybindings organized in clean TUI section cards with styled keycap badges.
"""

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

SECTIONS = [
    (
        "NAVIGATION (nnn-style)",
        [
            ("h  /  ←  /  Backspace", "Navigate to parent directory (..)"),
            ("l  /  →  /  Enter", "Open file or enter directory"),
            ("j  /  ↓", "Move selection down"),
            ("k  /  ↑", "Move selection up"),
            ("g  /  Home", "Jump to first item in list"),
            ("G  /  End", "Jump to last item in list"),
            (".  /  Ctrl+H", "Toggle hidden dotfiles"),
            ("~", "Navigate to Home directory"),
            ("Ctrl+L", "Edit path bar directly"),
            ("q", "Quit application"),
        ]
    ),
    (
        "COMMAND BAR & GRAMMAR",
        [
            ("/", "Instant local current-directory filter"),
            (">", "Recursive search via fd (<15ms response)"),
            (":", "Command mode (:mkdir, :touch, :rename, :delete, shell)"),
            ("r", "Quick inline rename / batch pattern rename"),
            ("Esc", "Cancel filter/search/command mode"),
        ]
    ),
    (
        "SELECTION & FILE OPERATIONS",
        [
            ("Space", "Toggle selection on focused item"),
            ("Ctrl+C", "Copy selected file(s) to clipboard"),
            ("Ctrl+X", "Cut selected file(s) to clipboard"),
            ("Ctrl+V", "Paste file(s) from clipboard"),
            ("x", "Move selection to Trash (GIO Trash API)"),
            ("Shift+X", "Permanently delete selection (with confirmation)"),
        ]
    ),
    (
        "PREVIEW & HELP",
        [
            ("Tab", "Toggle side-by-side preview pane"),
            ("?  /  F1", "Toggle this help overlay"),
        ]
    ),
]

class HelpOverlayWindow(Gtk.Window):
    def __init__(self, parent_win):
        super().__init__(title="weg — Keybinding Cheat Sheet")
        self.set_transient_for(parent_win)
        self.set_modal(True)
        self.set_default_size(680, 520)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)

        # Header Banner
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        brand = Gtk.Label(label="[ weg ]")
        brand.add_css_class("mode-badge")
        title = Gtk.Label(label="KEYBINDINGS CHEAT SHEET", xalign=0.0)
        title.add_css_class("path-label")

        header_box.append(brand)
        header_box.append(title)
        main_box.append(header_box)
        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Scrollable Cards Container
        cards_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        for sec_title, items in SECTIONS:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            card.add_css_class("help-card")

            card_title = Gtk.Label(label=sec_title, xalign=0.0)
            card_title.add_css_class("help-title")
            card.append(card_title)
            card.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

            grid = Gtk.Grid()
            grid.set_column_spacing(16)
            grid.set_row_spacing(6)

            for row_idx, (key_cap, desc) in enumerate(items):
                lbl_key = Gtk.Label(label=f" {key_cap} ", xalign=0.0)
                lbl_key.add_css_class("key-cap")
                grid.attach(lbl_key, 0, row_idx, 1, 1)

                lbl_desc = Gtk.Label(label=desc, xalign=0.0)
                lbl_desc.add_css_class("key-desc")
                grid.attach(lbl_desc, 1, row_idx, 1, 1)

            card.append(grid)
            cards_box.append(card)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(cards_box)
        scrolled.set_vexpand(True)
        main_box.append(scrolled)

        # Footer
        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        footer_info = Gtk.Label(label="Press Esc or 'q' to close", xalign=0.0)
        footer_info.set_hexpand(True)
        footer_info.add_css_class("status-bar")

        close_btn = Gtk.Button(label="Close (Esc)")
        close_btn.connect("clicked", lambda b: self.close())

        footer_box.append(footer_info)
        footer_box.append(close_btn)
        main_box.append(footer_box)

        self.set_child(main_box)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval in (Gdk.KEY_Escape, Gdk.KEY_q, Gdk.KEY_question):
            self.close()
            return True
        return False

def show_help_overlay(parent_win):
    win = HelpOverlayWindow(parent_win)
    win.present()
