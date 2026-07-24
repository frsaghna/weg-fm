#!/usr/bin/env /usr/bin/python3
"""
Automated unit & integration verification for Phase 5 Preview & Thumbnails.
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
from src.preview_pane import PreviewPaneWidget

class TestPhase5PreviewAndThumbnails(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_phase5_")
        self.sample_txt = os.path.join(self.tmp_dir, "sample.txt")
        with open(self.sample_txt, "w") as f:
            f.write("Line 1 preview test\nLine 2 preview test")

    def test_preview_pane_text_loading(self):
        pane = PreviewPaneWidget()
        pane.preview_file(self.sample_txt)
        text = pane.text_buffer.get_text(
            pane.text_buffer.get_start_iter(),
            pane.text_buffer.get_end_iter(),
            True
        )
        self.assertIn("Line 1 preview test", text)

    def test_tab_toggle_preview_in_window(self):
        win = WegWindow(Gtk.Application(application_id="fm.weg.TestP5"), initial_dir=self.tmp_dir)
        self.assertFalse(win.preview_pane.get_visible())

        win.toggle_preview()
        self.assertTrue(win.preview_pane.get_visible())

        win.toggle_preview()
        self.assertFalse(win.preview_pane.get_visible())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

if __name__ == "__main__":
    unittest.main()
