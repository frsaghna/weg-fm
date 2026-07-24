#!/usr/bin/env python3
import sys
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

class HelloWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="weg — Phase 0 Hello World")
        self.set_default_size(400, 200)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)

        label = Gtk.Label(label="Hello World — PyGObject + GTK4 is ready!")
        box.append(label)

        button = Gtk.Button(label="Close Window")
        button.connect("clicked", lambda x: self.close())
        box.append(button)

        self.set_child(box)

def on_activate(app):
    win = HelloWindow(app)
    win.present()
    # Auto close after 2 seconds for non-interactive automated test run
    if "--auto-close" in sys.argv:
        GLib.timeout_add(2000, app.quit)

def main():
    app = Gtk.Application(application_id="fm.weg.Phase0Hello")
    app.connect("activate", on_activate)
    return app.run([sys.argv[0]])

if __name__ == "__main__":
    sys.exit(main())
