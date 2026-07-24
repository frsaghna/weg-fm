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
        self.assertEqual(len(file_list.displayed_items), 2)
        # Subdir (directory) should come first, then file
        self.assertTrue(file_list.displayed_items[0].is_dir)
        self.assertEqual(file_list.displayed_items[0].name, "subdir")
        self.assertFalse(file_list.displayed_items[1].is_dir)
        self.assertEqual(file_list.displayed_items[1].name, "alpha.txt")

    def test_live_gfilemonitor_updates(self):
        updates = []
        loop = GLib.MainLoop()

        monitor = DirectoryMonitor(on_change_callback=lambda: updates.append("changed"))
        monitor.set_directory(self.tmp_dir)

        def trigger_file():
            new_file = os.path.join(self.tmp_dir, "beta_external.txt")
            with open(new_file, "w") as f:
                f.write("created externally")
            return False

        def check_done():
            if updates:
                loop.quit()
                return False
            return True

        GLib.timeout_add(50, trigger_file)
        GLib.timeout_add(100, check_done)
        GLib.timeout_add(1000, loop.quit)

        loop.run()
        monitor.stop()

        self.assertIn("changed", updates, "Live GFileMonitor update was not triggered on external file creation!")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

if __name__ == "__main__":
    unittest.main()
