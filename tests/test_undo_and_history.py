#!/usr/bin/python3
"""
Automated unit verification for Phase 8.1 (Atomic Multi-Level Undo/Redo)
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
from src.undo_manager import UndoManager, BatchRenameRecord, MoveRecord, CopyRecord, TrashRecord
from src.context_manager import ContextState

class TestUndoAndHistory(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_undo_test_")
        self.file1 = os.path.join(self.tmp_dir, "alpha.txt")
        self.file2 = os.path.join(self.tmp_dir, "beta.txt")
        with open(self.file1, "w") as f:
            f.write("test content 1")
        with open(self.file2, "w") as f:
            f.write("test content 2")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_atomic_batch_rename_undo(self):
        um = UndoManager()
        r1 = os.path.join(self.tmp_dir, "new_1.txt")
        r2 = os.path.join(self.tmp_dir, "new_2.txt")
        pairs = [(self.file1, r1), (self.file2, r2)]

        os.rename(self.file1, r1)
        os.rename(self.file2, r2)
        um.push(BatchRenameRecord(pairs))

        # Single 'u' undo press must atomically revert ALL renamed files
        ok, msg = um.undo()
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(self.file1))
        self.assertTrue(os.path.exists(self.file2))
        self.assertFalse(os.path.exists(r1))
        self.assertFalse(os.path.exists(r2))

        # Single 'redo' press must atomically re-apply ALL renames
        ok_redo, msg_redo = um.redo()
        self.assertTrue(ok_redo)
        self.assertFalse(os.path.exists(self.file1))
        self.assertFalse(os.path.exists(self.file2))
        self.assertTrue(os.path.exists(r1))
        self.assertTrue(os.path.exists(r2))

    def test_fallback_collision_rename_pairing_restoration(self):
        um = UndoManager()
        # Test batch rename where one file hit fallback _<n>.<ext>
        f_orig1 = os.path.join(self.tmp_dir, "custom_name.txt")
        f_orig2 = os.path.join(self.tmp_dir, "special.txt")
        open(f_orig1, "w").close()
        open(f_orig2, "w").close()

        # Simulate fallback pairing
        f_new1 = os.path.join(self.tmp_dir, "batch_1.txt")
        f_new2 = os.path.join(self.tmp_dir, "batch_2.txt")
        pairs = [(f_orig1, f_new1), (f_orig2, f_new2)]

        os.rename(f_orig1, f_new1)
        os.rename(f_orig2, f_new2)
        um.push(BatchRenameRecord(pairs))

        # Undo must restore exact original file pairs
        ok, msg = um.undo()
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(f_orig1))
        self.assertTrue(os.path.exists(f_orig2))
        self.assertFalse(os.path.exists(f_new1))
        self.assertFalse(os.path.exists(f_new2))

    def test_chained_and_cyclic_rename_undo(self):
        um = UndoManager()
        fa = os.path.join(self.tmp_dir, "file_a.txt")
        fb = os.path.join(self.tmp_dir, "file_b.txt")
        fc = os.path.join(self.tmp_dir, "file_c.txt")

        open(fa, "w").write("content A")
        open(fb, "w").write("content B")

        # Chained rename: b -> c, a -> b
        os.rename(fb, fc)
        os.rename(fa, fb)
        um.push(BatchRenameRecord([(fb, fc), (fa, fb)]))

        # Undo must restore fa and fb without collision
        ok, msg = um.undo()
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(fa))
        self.assertTrue(os.path.exists(fb))
        self.assertFalse(os.path.exists(fc))
        self.assertEqual(open(fa).read(), "content A")
        self.assertEqual(open(fb).read(), "content B")

    def test_undo_precondition_failure(self):
        um = UndoManager()
        renamed = os.path.join(self.tmp_dir, "beta_renamed.txt")
        os.rename(self.file1, renamed)
        um.push(BatchRenameRecord([(self.file1, renamed)]))

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
