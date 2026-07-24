#!/usr/bin/env /usr/bin/python3
"""
Automated unit & integration verification for Phase 4 Clipboard & DND Integration.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gio', '2.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, Gio, GLib

from src.window import WegWindow

class TestPhase4ClipboardAndDND(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_phase4_")
        self.dest_dir = os.path.join(self.tmp_dir, "dest")
        os.makedirs(self.dest_dir)

        self.test_file = os.path.join(self.tmp_dir, "sample.txt")
        with open(self.test_file, "w") as f:
            f.write("clipboard phase 4 sample")

    def test_clipboard_copy_and_paste_flow(self):
        app = Gtk.Application(application_id="fm.weg.TestP4")
        test_passed = []

        def on_activate(a):
            win = WegWindow(a, initial_dir=self.tmp_dir)
            win.present()

            # Select sample.txt and copy to clipboard
            win.file_list.selected_paths = {self.test_file}
            win.copy_selection_to_clipboard(action="copy")

            # Navigate to dest_dir and paste
            win.navigate_to(self.dest_dir)
            win.paste_from_clipboard()

            def check_pasted():
                pasted_file = os.path.join(self.dest_dir, "sample.txt")
                if os.path.exists(pasted_file):
                    test_passed.append("pasted")
                    app.quit()
                    return False
                return True

            GLib.timeout_add(200, check_pasted)
            GLib.timeout_add(2000, app.quit)

        app.connect("activate", on_activate)
        app.run([])

        self.assertIn("pasted", test_passed, "Clipboard file copy and paste failed to replicate file in destination dir!")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

if __name__ == "__main__":
    unittest.main()
