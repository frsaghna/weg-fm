"""
Interactive TUI Help Overlay Dialog for weg (triggered by '?' or ':help').
"""

import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

HELP_TEXT = """
┌─────────────────────────────────────────────────────────────┐
│                    weg — Keybindings & Help                 │
└─────────────────────────────────────────────────────────────┘

  NAVIGATION (nnn-style)
  ──────────────────────
  h / ← / Backspace  : Go to parent directory
  l / → / Enter      : Open file or enter directory
  j / ↓              : Move selection down
  k / ↑              : Move selection up
  g / Home           : Jump to first item
  G / End            : Jump to last item
  . / Ctrl+H         : Toggle hidden dotfiles
  ~                  : Go to Home directory
  Ctrl+L             : Edit path directly
  q                  : Quit application

  COMMAND BAR & GRAMMAR
  ─────────────────────
  /                  : Instant local current-dir filter
  >                  : Recursive search via fd (<15ms response)
  :                  : Command mode (:mkdir, :touch, :rename, :delete, shell)
  r                  : Inline rename / batch rename mode
  Esc                : Cancel filter/search/command mode

  SELECTION & FILE OPERATIONS
  ───────────────────────────
  Space              : Toggle selection on focused item
  Ctrl+C             : Copy selected file(s) to clipboard
  Ctrl+X             : Cut selected file(s) to clipboard
  Ctrl+V             : Paste file(s) from clipboard
  x                  : Move selection to Trash (GIO Trash API)
  Shift+X            : Permanent delete (with confirmation)

  PREVIEW & HELP
  ──────────────
  Tab                : Toggle side-by-side preview pane
  ? / F1             : Toggle this help overlay

  Press Esc or 'q' to close this help window.
"""

class HelpOverlayWindow(Gtk.Window):
    def __init__(self, parent_win):
        super().__init__(title="weg Help")
        self.set_transient_for(parent_win)
        self.set_modal(True)
        self.set_default_size(600, 480)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(16)
        box.set_margin_end(16)

        buffer = Gtk.TextBuffer()
        buffer.set_text(HELP_TEXT.strip())

        view = Gtk.TextView(buffer=buffer)
        view.set_editable(False)
        view.set_monospace(True)
        view.set_cursor_visible(False)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(view)
        scrolled.set_vexpand(True)
        box.append(scrolled)

        close_btn = Gtk.Button(label="Close (Esc)")
        close_btn.set_margin_top(8)
        close_btn.connect("clicked", lambda b: self.close())
        box.append(close_btn)

        self.set_child(box)

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
