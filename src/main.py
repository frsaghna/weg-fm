"""
Main application entry point for weg.
"""

import sys
import os
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

from src.window import WegWindow

class WegApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="fm.weg.Explorer")

    def do_activate(self):
        win = self.props.active_window
        if not win:
            start_dir = sys.argv[1] if len(sys.argv) > 1 and os.path.exists(sys.argv[1]) else None
            win = WegWindow(self, initial_dir=start_dir)
        win.present()
        if "--auto-test" in sys.argv:
            # Quit after 2 seconds during automated verification
            GLib.timeout_add(2000, self.quit)

def main():
    app = WegApplication()
    return app.run([sys.argv[0]] + [a for a in sys.argv[1:] if a != "--auto-test"])

if __name__ == "__main__":
    sys.exit(main())
