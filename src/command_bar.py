"""
Command line widget and grammar handler for weg.
Handles prefixes (/, >, :) and standalone commands (e.g. 'theme nord', 'mkdir foo', 'touch bar').
"""

import os
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk

KNOWN_COMMAND_VERBS = ("theme", "mkdir", "touch", "new", "rename", "mv", "delete", "rm", "help", "hint", "?")

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

        self.badge_label = Gtk.Label(label="NORMAL")
        self.badge_label.add_css_class("mode-badge")
        self.append(self.badge_label)

        self.prefix_label = Gtk.Label(label=":")
        self.entry = Gtk.Entry()
        self.entry.set_hexpand(True)
        self.entry.set_placeholder_text("Press /, >, or : for commands (e.g. 'theme nord', '/search')")

        self.append(self.prefix_label)
        self.append(self.entry)

        self.entry.connect("changed", self._on_changed)
        self.entry.connect("activate", self._on_activate)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.entry.add_controller(key_ctrl)

        self._update_badge()

    def activate_mode(self, prefix, initial_text=""):
        self.mode = prefix
        self.prefix_label.set_text(prefix)
        self.entry.set_text(initial_text)
        self.entry.set_position(-1)
        self.entry.grab_focus()
        self._update_badge()

    def deactivate(self, keep_filter=False):
        self.mode = None
        self.prefix_label.set_text(":")
        self.entry.set_text("")
        self.entry.set_placeholder_text("Press /, >, or : for commands (e.g. 'theme nord', '/search')")
        self._update_badge()
        if self.on_cancel:
            self.on_cancel(keep_filter=keep_filter)

    def _update_badge(self):
        for cls in ("mode-badge-filter", "mode-badge-search", "mode-badge-cmd"):
            self.badge_label.remove_css_class(cls)

        if self.mode == '/':
            self.badge_label.set_text("FILTER")
            self.badge_label.add_css_class("mode-badge-filter")
        elif self.mode == '>':
            self.badge_label.set_text("SEARCH")
            self.badge_label.add_css_class("mode-badge-search")
        elif self.mode == ':':
            self.badge_label.set_text("CMD")
            self.badge_label.add_css_class("mode-badge-cmd")
        else:
            self.badge_label.set_text("NORMAL")

    def _on_changed(self, entry):
        text = entry.get_text()

        # Auto-detect mode prefix or command verb if user typed directly into entry
        if not self.mode and text:
            if text.startswith('/'):
                self.mode = '/'
                self.prefix_label.set_text('/')
                text = text[1:]
                entry.set_text(text)
                entry.set_position(-1)
                self._update_badge()
                return
            elif text.startswith('>'):
                self.mode = '>'
                self.prefix_label.set_text('>')
                text = text[1:]
                entry.set_text(text)
                entry.set_position(-1)
                self._update_badge()
                return
            elif text.startswith(':'):
                self.mode = ':'
                self.prefix_label.set_text(':')
                text = text[1:]
                entry.set_text(text)
                entry.set_position(-1)
                self._update_badge()
                return
            else:
                # Check if first word is a known command verb (e.g. 'theme nord')
                first_word = text.split()[0].lower() if text.split() else ""
                if first_word in KNOWN_COMMAND_VERBS:
                    self.mode = ':'
                    self.prefix_label.set_text(':')
                    self._update_badge()
                    return
                else:
                    self.mode = '/'
                    self.prefix_label.set_text('/')
                    self._update_badge()

        if self.mode == '/':
            self.on_filter_change(text)
        elif self.mode == '>':
            if len(text) >= 1:
                self.on_search_query(text)
            else:
                self.on_filter_change("")

    def _on_activate(self, entry):
        text = entry.get_text().strip()
        if text.startswith(':'):
            text = text[1:].strip()
            self.mode = ':'

        first_word = text.split()[0].lower() if text.split() else ""

        if self.mode == ':' or first_word in KNOWN_COMMAND_VERBS:
            if text:
                self.on_command_execute(text)
            self.deactivate(keep_filter=False)
        elif self.mode in ('/', '>'):
            self.deactivate(keep_filter=True)
        else:
            if text:
                self.on_command_execute(text)
            self.deactivate(keep_filter=False)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.deactivate(keep_filter=False)
            return True
        return False
