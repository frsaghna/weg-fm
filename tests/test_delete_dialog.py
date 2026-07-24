#!/usr/bin/python3
"""
Automated unit verification for Custom TUI Delete Confirmation Dialog.
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
from src.delete_dialog import show_delete_confirmation, DeleteConfirmWindow

class TestDeleteConfirmationDialog(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_delete_test_")
        self.target_file = os.path.join(self.tmp_dir, "test_file.txt")
        with open(self.target_file, "w") as f:
            f.write("delete me")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_delete_dialog_key_confirm(self):
        app = Gtk.Application(application_id="fm.weg.TestDeleteDialog")
        win = WegWindow(app, initial_dir=self.tmp_dir)

        deleted = []
        def _on_confirm(targets):
            deleted.extend(targets)

        dlg = DeleteConfirmWindow(win, [self.target_file], _on_confirm)
        # Simulate pressing 'y' key
        handled = dlg._on_key_pressed(None, Gdk.KEY_y, 0, 0)
        self.assertTrue(handled)
        self.assertIn(self.target_file, deleted)

    def test_delete_dialog_key_cancel(self):
        app = Gtk.Application(application_id="fm.weg.TestDeleteDialog")
        win = WegWindow(app, initial_dir=self.tmp_dir)

        deleted = []
        def _on_confirm(targets):
            deleted.extend(targets)

        dlg = DeleteConfirmWindow(win, [self.target_file], _on_confirm)
        # Simulate pressing 'n' key
        handled = dlg._on_key_pressed(None, Gdk.KEY_n, 0, 0)
        self.assertTrue(handled)
        self.assertEqual(len(deleted), 0)

if __name__ == "__main__":
    unittest.main()
