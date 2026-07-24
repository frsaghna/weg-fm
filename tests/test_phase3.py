#!/usr/bin/env /usr/bin/python3
"""
Automated unit & integration verification for Phase 3 Command-Line Grammar (/, >, :).
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

class TestPhase3CommandGrammar(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_phase3_")
        # Create test items
        os.makedirs(os.path.join(self.tmp_dir, "Documents"))
        os.makedirs(os.path.join(self.tmp_dir, "Projects"))
        with open(os.path.join(self.tmp_dir, "notes.txt"), "w") as f:
            f.write("hello")
        with open(os.path.join(self.tmp_dir, "photo.jpg"), "w") as f:
            f.write("img")

    def test_local_filter_slash(self):
        win = WegWindow(Gtk.Application(application_id="fm.weg.TestP3"), initial_dir=self.tmp_dir)
        self.assertEqual(len(win.file_list.displayed_items), 4)

        # Filter for 'proj'
        win.file_list.filter_local("proj")
        self.assertEqual(len(win.file_list.displayed_items), 1)
        self.assertEqual(win.file_list.displayed_items[0].name, "Projects")

        # Clear filter
        win.file_list.filter_local("")
        self.assertEqual(len(win.file_list.displayed_items), 4)

    def test_create_file_and_folder_commands(self):
        win = WegWindow(Gtk.Application(application_id="fm.weg.TestP3"), initial_dir=self.tmp_dir)
        
        # Test :new folder Assets
        win.execute_command("new folder Assets")
        self.assertTrue(os.path.isdir(os.path.join(self.tmp_dir, "Assets")))

        # Test :new file script.py
        win.execute_command("new file script.py")
        self.assertTrue(os.path.isfile(os.path.join(self.tmp_dir, "script.py")))

    def test_rename_command(self):
        win = WegWindow(Gtk.Application(application_id="fm.weg.TestP3"), initial_dir=self.tmp_dir)
        
        # Focus notes.txt and rename to memo.txt
        note_path = os.path.join(self.tmp_dir, "notes.txt")
        win.file_list.selected_paths = {note_path}
        win.execute_command("rename memo.txt")
        self.assertTrue(os.path.exists(os.path.join(self.tmp_dir, "memo.txt")))
        self.assertFalse(os.path.exists(note_path))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

if __name__ == "__main__":
    unittest.main()
