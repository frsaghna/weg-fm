#!/usr/bin/python3
"""
Automated unit & integration verification for nnn-style Multi-Contexts / Tabs (1-8).
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
from src.context_manager import ContextManager

class TestMultiContextManager(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_context_test_")
        self.sub_dir1 = os.path.join(self.tmp_dir, "sub1")
        self.sub_dir2 = os.path.join(self.tmp_dir, "sub2")
        os.makedirs(self.sub_dir1)
        os.makedirs(self.sub_dir2)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_context_manager_state(self):
        cm = ContextManager(initial_dir=self.tmp_dir, total_contexts=8)
        self.assertEqual(cm.active_id, 1)

        # Context 1 navigates to sub1
        cm.get_active().current_dir = self.sub_dir1

        # Switch to Context 2 and navigate to sub2
        cm.set_active_context(2)
        self.assertEqual(cm.active_id, 2)
        cm.get_active().current_dir = self.sub_dir2

        # Switch back to Context 1
        cm.set_active_context(1)
        self.assertEqual(cm.get_active().current_dir, self.sub_dir1)

    def test_window_context_switching_and_keys(self):
        app = Gtk.Application(application_id="fm.weg.TestContexts")
        win = WegWindow(app, initial_dir=self.tmp_dir)

        # Context 1 starts in tmp_dir
        self.assertEqual(win.context_mgr.active_id, 1)

        # Navigate Context 1 to sub1
        win.navigate_to(self.sub_dir1)
        self.assertEqual(win.current_dir, self.sub_dir1)

        # Press key '2' to switch to Context 2
        handled = win._on_key_pressed(None, Gdk.KEY_2, 0, 0)
        self.assertTrue(handled)
        self.assertEqual(win.context_mgr.active_id, 2)
        self.assertEqual(win.current_dir, self.tmp_dir) # Context 2 starts in initial_dir

        # Navigate Context 2 to sub2
        win.navigate_to(self.sub_dir2)
        self.assertEqual(win.current_dir, self.sub_dir2)

        # Press key '1' to switch back to Context 1
        win._on_key_pressed(None, Gdk.KEY_1, 0, 0)
        self.assertEqual(win.context_mgr.active_id, 1)
        self.assertEqual(win.current_dir, self.sub_dir1)

if __name__ == "__main__":
    unittest.main()
