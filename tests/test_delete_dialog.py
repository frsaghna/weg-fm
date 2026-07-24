#!/usr/bin/python3
"""
Automated unit verification for Minimal Safe Delete Confirmation Dialog.
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
from src.delete_dialog import DeleteConfirmWindow

class TestDeleteConfirmationDialog(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_delete_test_")
        self.target_file = os.path.join(self.tmp_dir, "test_file.txt")
        with open(self.target_file, "w") as f:
            f.write("delete me")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_delete_dialog_key_y(self):
        app = Gtk.Application(application_id="fm.weg.TestDeleteDialog")
        win = WegWindow(app, initial_dir=self.tmp_dir)

        deleted = []
        def _on_confirm(targets):
            deleted.extend(targets)

        dlg = DeleteConfirmWindow(win, [self.target_file], _on_confirm)
        handled = dlg._on_key_pressed(None, Gdk.KEY_y, 0, 0)
        self.assertTrue(handled)
        self.assertIn(self.target_file, deleted)

    def test_delete_dialog_key_n_and_esc(self):
        app = Gtk.Application(application_id="fm.weg.TestDeleteDialog")
        win = WegWindow(app, initial_dir=self.tmp_dir)

        deleted = []
        def _on_confirm(targets):
            deleted.extend(targets)

        dlg = DeleteConfirmWindow(win, [self.target_file], _on_confirm)
        handled = dlg._on_key_pressed(None, Gdk.KEY_n, 0, 0)
        self.assertTrue(handled)
        self.assertEqual(len(deleted), 0)

        handled_esc = dlg._on_key_pressed(None, Gdk.KEY_Escape, 0, 0)
        self.assertTrue(handled_esc)
        self.assertEqual(len(deleted), 0)

    def test_delete_dialog_arrow_focus(self):
        app = Gtk.Application(application_id="fm.weg.TestDeleteDialog")
        win = WegWindow(app, initial_dir=self.tmp_dir)

        dlg = DeleteConfirmWindow(win, [self.target_file], lambda t: None)
        # Test arrow right/l moves focus to delete_btn
        dlg._on_key_pressed(None, Gdk.KEY_Right, 0, 0)
        self.assertEqual(dlg.get_focus(), dlg.delete_btn)

        # Test arrow left/h moves focus back to cancel_btn
        dlg._on_key_pressed(None, Gdk.KEY_Left, 0, 0)
        self.assertEqual(dlg.get_focus(), dlg.cancel_btn)

if __name__ == "__main__":
    unittest.main()
