#!/usr/bin/python3
"""
Automated unit verification for Phase 8.3 (Frecency-based Quick Jump :z).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

from src.window import WegWindow
from src.frecency import FrecencyTracker

class TestFrecencyQuickJump(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_frecency_test_")
        self.json_file = os.path.join(self.tmp_dir, "frecency.json")

        self.dir_projects = os.path.join(self.tmp_dir, "my_projects")
        self.dir_downloads = os.path.join(self.tmp_dir, "downloads")
        os.makedirs(self.dir_projects)
        os.makedirs(self.dir_downloads)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_frecency_scoring_and_query(self):
        ft = FrecencyTracker(storage_path=self.json_file)

        # Visit projects 3 times, downloads 1 time
        ft.record_visit(self.dir_projects)
        ft.record_visit(self.dir_projects)
        ft.record_visit(self.dir_projects)
        ft.record_visit(self.dir_downloads)

        # Query fragment 'proj' should match my_projects
        target = ft.query("proj")
        self.assertEqual(target, self.dir_projects)

        # Query fragment 'down' should match downloads
        target_down = ft.query("down")
        self.assertEqual(target_down, self.dir_downloads)

    def test_window_z_command(self):
        app = Gtk.Application(application_id="fm.weg.TestFrecencyWindow")
        win = WegWindow(app, initial_dir=self.tmp_dir)
        win.frecency = FrecencyTracker(storage_path=self.json_file)

        # Record visits
        win.navigate_to(self.dir_projects)
        win.navigate_to(self.dir_downloads)

        # Execute :z proj
        win.execute_command("z proj")
        self.assertEqual(win.current_dir, self.dir_projects)

        # Execute :z down
        win.execute_command("z down")
        self.assertEqual(win.current_dir, self.dir_downloads)

if __name__ == "__main__":
    unittest.main()
