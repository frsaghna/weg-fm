#!/usr/bin/python3
"""
Automated unit verification for multi-character typing in filter mode.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from src.window import WegWindow

class TestFilterTyping(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_filter_test_")
        for f in ["alpha.py", "beta.txt", "alpha_two.py"]:
            open(os.path.join(self.tmp_dir, f), "w").close()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_filter_multi_character_typing(self):
        app = Gtk.Application(application_id="fm.weg.TestFilterTyping")
        win = WegWindow(app, initial_dir=self.tmp_dir)

        # Activate filter mode
        win.command_bar.activate_mode('/')
        entry = win.command_bar.entry

        # Simulate typing multiple characters "alpha"
        entry.set_text("alpha")
        # Ensure focus remains inside entry and is not stolen by list row
        root = entry.get_root()
        if root:
            self.assertIn(type(root.get_focus()).__name__, ("Entry", "GtkEntry", "Text", "GtkText"))

        # Verify displayed items are filtered to 2 matching files
        self.assertEqual(len(win.file_list.displayed_items), 2)
        displayed_names = [item.name for item in win.file_list.displayed_items]
        self.assertIn("alpha.py", displayed_names)
        self.assertIn("alpha_two.py", displayed_names)

if __name__ == "__main__":
    unittest.main()
