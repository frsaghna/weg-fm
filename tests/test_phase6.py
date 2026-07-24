#!/usr/bin/env /usr/bin/python3
"""
Automated unit & integration verification for Phase 6 Deletion & Data Safety.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk

from src.window import WegWindow

class TestPhase6DeletionAndSafety(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_phase6_", dir=os.path.expanduser("~"))
        self.trash_item = os.path.join(self.tmp_dir, "trash_me.txt")
        with open(self.trash_item, "w") as f:
            f.write("temporary file for trash test")

        self.delete_item = os.path.join(self.tmp_dir, "delete_me.txt")
        with open(self.delete_item, "w") as f:
            f.write("temporary file for permanent delete test")

    def test_gio_trash(self):
        win = WegWindow(Gtk.Application(application_id="fm.weg.TestP6"), initial_dir=self.tmp_dir)
        win.file_list.selected_paths = {self.trash_item}
        win.move_selection_to_trash()

        self.assertFalse(os.path.exists(self.trash_item), "File was not moved to trash!")

    def test_permanent_delete(self):
        win = WegWindow(Gtk.Application(application_id="fm.weg.TestP6"), initial_dir=self.tmp_dir)
        win.file_list.selected_paths = {self.delete_item}
        win.permanent_delete_selection(confirm_bypass=True)

        self.assertFalse(os.path.exists(self.delete_item), "File was not permanently deleted!")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

if __name__ == "__main__":
    unittest.main()
