#!/usr/bin/env /usr/bin/python3
"""
Automated tests for nnn-style keyboard navigation and CommandBar fixes.
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

class TestNnnNavigationAndCmdBar(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_nnn_test_")
        self.sub_dir = os.path.join(self.tmp_dir, "alpha_dir")
        os.makedirs(self.sub_dir)
        
        self.hidden_file = os.path.join(self.tmp_dir, ".secret")
        with open(self.hidden_file, "w") as f:
            f.write("hidden")

        self.normal_file = os.path.join(self.tmp_dir, "zebra_file.txt")
        with open(self.normal_file, "w") as f:
            f.write("visible")

    def test_hidden_files_toggle(self):
        win = WegWindow(Gtk.Application(application_id="fm.weg.TestNnn"), initial_dir=self.tmp_dir)
        names_default = [item.name for item in win.file_list.displayed_items]
        self.assertNotIn(".secret", names_default, "Hidden dotfile showed by default!")

        # Toggle hidden files
        win.file_list.toggle_hidden_files()
        names_hidden = [item.name for item in win.file_list.displayed_items]
        self.assertIn(".secret", names_hidden, "Hidden dotfile not visible after toggle!")

    def test_command_bar_auto_detect_and_execute(self):
        win = WegWindow(Gtk.Application(application_id="fm.weg.TestNnn"), initial_dir=self.tmp_dir)
        
        # Test typing ':mkdir new_folder' directly
        win.command_bar.entry.set_text(":mkdir new_folder")
        win.command_bar._on_activate(win.command_bar.entry)
        self.assertTrue(os.path.isdir(os.path.join(self.tmp_dir, "new_folder")))

        # Test typing ':touch new_file.py' directly
        win.command_bar.entry.set_text(":touch new_file.py")
        win.command_bar._on_activate(win.command_bar.entry)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp_dir, "new_file.py")))

    def test_jumps_and_navigation(self):
        win = WegWindow(Gtk.Application(application_id="fm.weg.TestNnn"), initial_dir=self.tmp_dir)
        
        # Jump to first
        win.file_list.jump_to_first()
        self.assertEqual(win.file_list.get_focused_item().name, "alpha_dir")

        # Jump to last
        win.file_list.jump_to_last()
        self.assertEqual(win.file_list.get_focused_item().name, "zebra_file.txt")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

if __name__ == "__main__":
    unittest.main()
