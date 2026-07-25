#!/usr/bin/python3
"""
Automated unit verification for Phase 8.1 (Atomic Multi-Level Undo/Redo),
Phase 8.2 (Browser-Style Directory History), and XDG Trash Undo Restoration.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, Gio

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

        ok, msg = um.undo()
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(self.file1))
        self.assertTrue(os.path.exists(self.file2))
        self.assertFalse(os.path.exists(r1))
        self.assertFalse(os.path.exists(r2))

        ok_redo, msg_redo = um.redo()
        self.assertTrue(ok_redo)
        self.assertFalse(os.path.exists(self.file1))
        self.assertFalse(os.path.exists(self.file2))
        self.assertTrue(os.path.exists(r1))
        self.assertTrue(os.path.exists(r2))

    def test_trash_and_undo_restoration(self):
        # Create test file in ~/.cache to support XDG Trash (tmpfs /tmp does not support trash)
        user_cache = os.path.expanduser("~/.cache/weg_test_trash_dir")
        os.makedirs(user_cache, exist_ok=True)
        photo_path = os.path.join(user_cache, "photo_sample.jpg")
        with open(photo_path, "w") as f:
            f.write("photo data content")

        um = UndoManager()
        gfile = Gio.File.new_for_path(photo_path)
        gfile.trash(None)
        self.assertFalse(os.path.exists(photo_path))

        um.push(TrashRecord([photo_path]))

        # Undo must find .trashinfo and restore photo_sample.jpg to photo_path
        ok, msg = um.undo()
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(photo_path))
        self.assertIn("restored 1 item(s)", msg)

        import shutil
        shutil.rmtree(user_cache, ignore_errors=True)

    def test_fallback_collision_rename_pairing_restoration(self):
        um = UndoManager()
        f_orig1 = os.path.join(self.tmp_dir, "custom_name.txt")
        f_orig2 = os.path.join(self.tmp_dir, "special.txt")
        with open(f_orig1, "w") as f:
            f.write("content 1")
        with open(f_orig2, "w") as f:
            f.write("content 2")

        f_new1 = os.path.join(self.tmp_dir, "batch_1.txt")
        f_new2 = os.path.join(self.tmp_dir, "batch_2.txt")
        pairs = [(f_orig1, f_new1), (f_orig2, f_new2)]

        os.rename(f_orig1, f_new1)
        os.rename(f_orig2, f_new2)
        um.push(BatchRenameRecord(pairs))

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

        with open(fa, "w") as f:
            f.write("content A")
        with open(fb, "w") as f:
            f.write("content B")

        os.rename(fb, fc)
        os.rename(fa, fb)
        um.push(BatchRenameRecord([(fb, fc), (fa, fb)]))

        ok, msg = um.undo()
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(fa))
        self.assertTrue(os.path.exists(fb))
        self.assertFalse(os.path.exists(fc))

    def test_mid_batch_failure_rollback(self):
        fa = os.path.join(self.tmp_dir, "file_a.txt")
        fb = os.path.join(self.tmp_dir, "file_b.txt")
        with open(fa, "w") as f:
            f.write("content A")
        with open(fb, "w") as f:
            f.write("content B")

        r_a = os.path.join(self.tmp_dir, "new_a.txt")
        r_b = os.path.join(self.tmp_dir, "new_b.txt")
        os.rename(fa, r_a)
        os.rename(fb, r_b)

        record = BatchRenameRecord([(fa, r_a), (fb, r_b)])

        orig_rename = os.rename
        call_count = 0
        def mock_rename(src, dst):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise PermissionError("Simulated disk write error")
            return orig_rename(src, dst)

        import unittest.mock as mock
        with mock.patch("os.rename", side_effect=mock_rename):
            ok, msg = record.undo()
            self.assertFalse(ok)
            self.assertIn("Undo failed mid-batch", msg)

        self.assertTrue(os.path.exists(r_a))
        self.assertTrue(os.path.exists(r_b))
        self.assertFalse(any(".weg_undo_" in name for name in os.listdir(self.tmp_dir)))

    def test_undo_precondition_failure(self):
        um = UndoManager()
        renamed = os.path.join(self.tmp_dir, "beta_renamed.txt")
        os.rename(self.file1, renamed)
        um.push(BatchRenameRecord([(self.file1, renamed)]))

        os.remove(renamed)

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

        prev1 = ctx.go_back()
        self.assertEqual(prev1, sub1)
        self.assertEqual(ctx.current_dir, sub1)

        prev2 = ctx.go_back()
        self.assertEqual(prev2, self.tmp_dir)
        self.assertEqual(ctx.current_dir, self.tmp_dir)

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

        win._on_key_pressed(None, Gdk.KEY_h, 0, Gdk.ModifierType.ALT_MASK)
        self.assertEqual(win.current_dir, self.tmp_dir)

        win._on_key_pressed(None, Gdk.KEY_l, 0, Gdk.ModifierType.ALT_MASK)
        self.assertEqual(win.current_dir, sub1)

if __name__ == "__main__":
    unittest.main()
