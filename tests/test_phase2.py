#!/usr/bin/env /usr/bin/python3
"""
Automated unit & integration verification for Phase 2 Core Navigation Shell & Live GFileMonitor updates.
"""

import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gio, GLib

from src.window import WegWindow
from src.file_list import FileListWidget
from src.monitor import DirectoryMonitor

class TestPhase2NavigationShell(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_test_")
        self.sub_dir = os.path.join(self.tmp_dir, "subdir")
        os.makedirs(self.sub_dir)
        self.file1 = os.path.join(self.tmp_dir, "alpha.txt")
        with open(self.file1, "w") as f:
            f.write("hello")

    def test_file_list_sorting_and_navigation(self):
        status_updates = []
        file_list = FileListWidget(
            on_open_directory=lambda p: None,
            on_status_change=lambda s: status_updates.append(s)
        )
        loaded = file_list.load_directory(self.tmp_dir)
        self.assertTrue(loaded)
        self.assertEqual(len(file_list.items), 2)
        # Subdir (directory) should come first, then file
        self.assertTrue(file_list.items[0].is_dir)
        self.assertEqual(file_list.items[0].name, "subdir")
        self.assertFalse(file_list.items[1].is_dir)
        self.assertEqual(file_list.items[1].name, "alpha.txt")

    def test_live_gfilemonitor_updates(self):
        app = Gtk.Application(application_id="fm.weg.TestMonitor")
        updates_received = []

        def on_activate(a):
            win = WegWindow(a, initial_dir=self.tmp_dir)
            win.present()

            # Verify initial count
            self.assertEqual(len(win.file_list.items), 2)

            # Create a new file externally
            new_file = os.path.join(self.tmp_dir, "beta_external.txt")
            with open(new_file, "w") as f:
                f.write("created externally")

            # Wait for GFileMonitor to notify GLib mainloop
            def check_update():
                item_names = [item.name for item in win.file_list.items]
                if "beta_external.txt" in item_names:
                    updates_received.append("updated")
                    app.quit()
                    return False
                return True

            GLib.timeout_add(100, check_update)
            # Timeout safety after 3 seconds
            GLib.timeout_add(3000, app.quit)

        app.connect("activate", on_activate)
        app.run([])
        self.assertIn("updated", updates_received, "Live GFileMonitor update was not triggered on external file creation!")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

if __name__ == "__main__":
    unittest.main()
