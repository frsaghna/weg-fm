#!/usr/bin/python3
"""
Automated unit verification for Phase 9 Reliability Hardening:
  - Symlink & broken symlink detection without stat crash
  - Symlink deletion safety (unlinks pointer without modifying target)
  - Inline Permission Denied handling
"""

import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

from src.window import WegWindow
from src.file_list import FileListWidget, FileItem, get_file_details

class TestPhase9Reliability(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_phase9_")
        
        # 1. Real target file & directory
        self.target_file = os.path.join(self.tmp_dir, "real_target.txt")
        with open(self.target_file, "w") as f:
            f.write("target data")

        self.target_dir = os.path.join(self.tmp_dir, "real_dir")
        os.makedirs(self.target_dir)

        # 2. Valid symlink to file & directory
        self.link_file = os.path.join(self.tmp_dir, "link_to_file.txt")
        os.symlink(self.target_file, self.link_file)

        self.link_dir = os.path.join(self.tmp_dir, "link_to_dir")
        os.symlink(self.target_dir, self.link_dir)

        # 3. Broken symlink
        self.broken_link = os.path.join(self.tmp_dir, "broken_link.txt")
        os.symlink(os.path.join(self.tmp_dir, "nonexistent.txt"), self.broken_link)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_symlink_detection_and_stat_safety(self):
        # Broken symlinks must not crash get_file_details
        details = get_file_details(self.broken_link, is_dir=False)
        self.assertTrue(isinstance(details, str))

        widget = FileListWidget(on_open_directory=None, on_status_change=None)
        widget.load_directory(self.tmp_dir)

        items_map = {item.name: item for item in widget.all_items}
        self.assertIn("link_to_file.txt", items_map)
        self.assertIn("broken_link.txt", items_map)

        self.assertTrue(items_map["link_to_file.txt"].is_symlink)
        self.assertFalse(items_map["link_to_file.txt"].is_broken_symlink)

        self.assertTrue(items_map["broken_link.txt"].is_symlink)
        self.assertTrue(items_map["broken_link.txt"].is_broken_symlink)

    def test_symlink_permanent_delete_safety(self):
        app = Gtk.Application(application_id="fm.weg.TestP9Delete")
        win = WegWindow(app, initial_dir=self.tmp_dir)

        # Permanently delete the directory symlink
        self.assertTrue(os.path.islink(self.link_dir))
        self.assertTrue(os.path.exists(self.target_dir))

        win._do_permanent_delete([self.link_dir])

        # Symlink pointer must be unlinked...
        self.assertFalse(os.path.islink(self.link_dir))
        # ...but target directory MUST remain 100% intact!
        self.assertTrue(os.path.exists(self.target_dir))

    def test_unreadable_directory_permission_denied_state(self):
        unreadable_dir = os.path.join(self.tmp_dir, "restricted_dir")
        os.makedirs(unreadable_dir)
        os.chmod(unreadable_dir, 0000)

        widget = FileListWidget(on_open_directory=None, on_status_change=None)
        widget.load_directory(unreadable_dir)

        self.assertEqual(len(widget.displayed_items), 1)
        self.assertIn("Permission Denied", widget.displayed_items[0].name)

        # Clean up permissions for teardown
        os.chmod(unreadable_dir, 0o755)

if __name__ == "__main__":
    unittest.main()
