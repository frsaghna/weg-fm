#!/usr/bin/python3
"""
Automated unit verification for Phase 8.1 (Multi-Level Undo/Redo)
and Phase 8.2 (Browser-Style Directory History).
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
from src.undo_manager import UndoManager, RenameRecord, MoveRecord, CopyRecord, TrashRecord
from src.context_manager import ContextState

class TestUndoAndHistory(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_undo_test_")
        self.file1 = os.path.join(self.tmp_dir, "alpha.txt")
        with open(self.file1, "w") as f:
            f.write("test content")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_undo_rename(self):
        um = UndoManager()
        renamed = os.path.join(self.tmp_dir, "beta.txt")
        os.rename(self.file1, renamed)
        um.push(RenameRecord(self.file1, renamed))

        # Undo rename
        ok, msg = um.undo()
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(self.file1))
        self.assertFalse(os.path.exists(renamed))

        # Redo rename
        ok, msg = um.redo()
        self.assertTrue(ok)
        self.assertFalse(os.path.exists(self.file1))
        self.assertTrue(os.path.exists(renamed))

    def test_undo_precondition_failure(self):
        um = UndoManager()
        renamed = os.path.join(self.tmp_dir, "beta.txt")
        os.rename(self.file1, renamed)
        um.push(RenameRecord(self.file1, renamed))

        # Remove renamed file externally
        os.remove(renamed)

        # Undo must fail gracefully without crashing
        ok, msg = um.undo()
        self.assertFalse(ok)
        self.assertIn("no longer exists", msg)

    def test_directory_history(self):
        ctx = ContextState(1, self.tmp_dir)
        sub1 = os.path.join(self.tmp_dir, "sub1")
        sub2 = os.path.join(self.tmp_dir, "sub2")
        os.makedirs(sub1)
        os.makedirs(sub2)

        ctx.push_history(sub1)
        self.assertEqual(ctx.current_dir, sub1)

        ctx.push_history(sub2)
        self.assertEqual(ctx.current_dir, sub2)

        # Go back
        prev1 = ctx.go_back()
        self.assertEqual(prev1, sub1)
        self.assertEqual(ctx.current_dir, sub1)

        prev2 = ctx.go_back()
        self.assertEqual(prev2, self.tmp_dir)
        self.assertEqual(ctx.current_dir, self.tmp_dir)

        # Go forward
        nxt1 = ctx.go_forward()
        self.assertEqual(nxt1, sub1)
        self.assertEqual(ctx.current_dir, sub1)

    def test_window_undo_and_history_keybindings(self):
        app = Gtk.Application(application_id="fm.weg.TestUndoHistoryWindow")
        win = WegWindow(app, initial_dir=self.tmp_dir)

        sub1 = os.path.join(self.tmp_dir, "sub1")
        os.makedirs(sub1)

        win.navigate_to(sub1)
        self.assertEqual(win.current_dir, sub1)

        # Press Alt+Left / Alt+h to go back
        win._on_key_pressed(None, Gdk.KEY_h, 0, Gdk.ModifierType.ALT_MASK)
        self.assertEqual(win.current_dir, self.tmp_dir)

        # Press Alt+Right / Alt+l to go forward
        win._on_key_pressed(None, Gdk.KEY_l, 0, Gdk.ModifierType.ALT_MASK)
        self.assertEqual(win.current_dir, sub1)

if __name__ == "__main__":
    unittest.main()
