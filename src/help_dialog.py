"""
Structured LazyVim / Neovim Which-Key style Help Overlay Dialog.
"""

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

SECTIONS = [
    (
        "NAVIGATION & VIM MOTIONS",
        [
            ("1  -  8", "Switch nnn-style context / tab (1-8, top-right indicator)"),
            ("h  /  ←  /  Backspace", "Navigate to parent directory (..)"),
            ("l  /  →  /  Enter", "Open file or enter directory"),
            ("j  /  ↓", "Move selection down"),
            ("k  /  ↑", "Move selection up"),
            ("gg", "Jump to top of file list"),
            ("G  /  End", "Jump to bottom of file list"),
            ("Ctrl+D", "Scroll half-page down (10 items)"),
            ("Ctrl+U", "Scroll half-page up (10 items)"),
            (".  /  Ctrl+H", "Toggle hidden dotfiles"),
            ("~", "Navigate to Home directory"),
            ("Ctrl+L", "Edit path bar directly"),
            ("q", "Quit application"),
        ]
    ),
    (
        "TELESCOPE & COMMAND BAR",
        [
            ("/", "Instant local current-directory live filter"),
            (">", "Recursive search via fd (<15ms response)"),
            (":", "Neovim command mode (:mkdir, :touch, :rename, :theme)"),
            ("r", "Quick inline rename / batch pattern rename"),
            ("Esc", "Cancel filter/search/command mode"),
        ]
    ),
    (
        "BUILT-IN ':' COMMANDS",
        [
            (":mkdir <name>", "Create a new folder in current directory"),
            (":touch <name>", "Create a new empty file in current directory"),
            (":rename <new_name>", "Rename selection (supports '{n}' for batch numbering)"),
            (":delete  /  :rm", "Permanently delete active selection"),
            (":theme", "Open interactive TUI Theme Selector menu"),
            (":theme <name>", "Switch theme (catppuccin, nord, tokyonight, gruvbox, dracula, matrix)"),
            (":help  /  :hint", "Open this Which-Key cheat sheet"),
            ("<any_shell_cmd>", "Execute shell command in current directory (e.g. :chmod +x script.sh)"),
        ]
    ),
    (
        "SELECTION & FILE OPERATIONS",
        [
            ("Space", "Toggle selection on focused item (LazyVim leader)"),
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
        super().__init__(title="Keybindings & Command Reference")
        self.set_transient_for(parent_win)
        self.set_modal(True)
        self.set_default_size(740, 580)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)

        # Header Banner
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title = Gtk.Label(label="LAZYVIM KEYBINDINGS & COMMAND REFERENCE", xalign=0.0)
        title.add_css_class("path-label")

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
