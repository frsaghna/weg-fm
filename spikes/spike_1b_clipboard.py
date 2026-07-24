#!/usr/bin/env /usr/bin/python3
"""
Spike 1b: Clipboard MIME Round-Trip Spike with Nautilus.
Tests setting and reading `x-special/gnome-copied-files` on Gdk.Clipboard.
"""

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gdk, Gio, GLib

class ClipboardSpikeWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Spike 1b: Clipboard MIME Test")
        self.set_default_size(550, 380)

        self.display = Gdk.Display.get_default()
        self.clipboard = self.display.get_clipboard()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        # Test file setup
        self.test_file_path = "/tmp/weg_clipboard_test.txt"
        with open(self.test_file_path, "w") as f:
            f.write("Clipboard test file from weg spike\n")

        # Copy button
        btn_copy = Gtk.Button(label=f"Copy '{self.test_file_path}' as x-special/gnome-copied-files")
        btn_copy.connect("clicked", self.on_copy_clicked)
        box.append(btn_copy)

        # Read button
        btn_read = Gtk.Button(label="Read Current Clipboard Contents")
        btn_read.connect("clicked", self.on_read_clicked)
        box.append(btn_read)

        # Log view
        self.log_buffer = Gtk.TextBuffer()
        self.log_view = Gtk.TextView(buffer=self.log_buffer)
        self.log_view.set_editable(False)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.log_view)
        scrolled.set_vexpand(True)
        box.append(scrolled)

        self.set_child(box)
        self.log("Ready. Use buttons to copy file onto clipboard or read from clipboard.")

    def log(self, text):
        print(f"[Clipboard Spike] {text}")
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, text + "\n")

    def on_copy_clicked(self, btn):
        gfile = Gio.File.new_for_path(self.test_file_path)
        uri = gfile.get_uri()
        # x-special/gnome-copied-files format: "copy\nfile:///path\0"
        payload_str = f"copy\n{uri}\0"
        payload_bytes = payload_str.encode('utf-8')
        gbytes = GLib.Bytes.new(payload_bytes)

        # Provide both x-special/gnome-copied-files AND Gdk.FileList for maximum compatibility
        gnome_provider = Gdk.ContentProvider.new_for_bytes("x-special/gnome-copied-files", gbytes)
        file_list = Gdk.FileList.new_from_list([gfile])
        file_list_provider = Gdk.ContentProvider.new_for_value(file_list)
        
        union_provider = Gdk.ContentProvider.new_union([gnome_provider, file_list_provider])
        self.clipboard.set_content(union_provider)
        self.log(f"COPIED to clipboard: payload='{payload_str.strip()}' MIME=x-special/gnome-copied-files")

    def on_read_clicked(self, btn):
        formats = self.clipboard.get_formats()
        mime_types = formats.get_mime_types()
        self.log(f"Clipboard Available MIME types: {mime_types}")

        if "x-special/gnome-copied-files" in mime_types:
            self.clipboard.read_async(["x-special/gnome-copied-files"], GLib.PRIORITY_DEFAULT, None, self._on_read_stream_done, None)
        elif formats.contain_gtype(Gdk.FileList):
            self.clipboard.read_value_async(Gdk.FileList, GLib.PRIORITY_DEFAULT, None, self._on_read_file_list_done, None)
        else:
            self.log("No gnome-copied-files or GdkFileList found on clipboard.")

    def _on_read_stream_done(self, clipboard, result, user_data):
        try:
            stream, mime_type = clipboard.read_finish(result)
            if stream:
                gbytes = stream.read_bytes(4096, None)
                data = gbytes.get_data().decode('utf-8', errors='replace').rstrip('\x00')
                lines = data.split('\n')
                action = lines[0] if len(lines) > 0 else "unknown"
                uris = lines[1:] if len(lines) > 1 else []
                self.log(f"READ {mime_type} -> Action: '{action}', URIs: {uris}")
            else:
                self.log("READ returned empty stream.")
        except Exception as e:
            self.log(f"ERROR reading stream: {e}")

    def _on_read_file_list_done(self, clipboard, result, user_data):
        try:
            val = clipboard.read_value_finish(result)
            if isinstance(val, Gdk.FileList):
                paths = [f.get_path() for f in val.get_files()]
                self.log(f"READ Gdk.FileList -> Paths: {paths}")
            else:
                self.log(f"READ Gdk.FileList -> Got value: {val}")
        except Exception as e:
            self.log(f"ERROR reading file list: {e}")

def main():
    app = Gtk.Application(application_id="fm.weg.Spike1b")
    def on_activate(a):
        win = ClipboardSpikeWindow(a)
        win.present()
        if "--auto-test" in sys.argv:
            # Trigger copy, then read, then quit
            GLib.timeout_add(200, lambda: win.on_copy_clicked(None))
            GLib.timeout_add(500, lambda: win.on_read_clicked(None))
            GLib.timeout_add(1200, a.quit)
    app.connect("activate", on_activate)
    return app.run([sys.argv[0]])

if __name__ == "__main__":
    sys.exit(main())
