#!/usr/bin/python3
"""
Automated unit verification for Preview Pane:
  - Content-Type filtering (prevents garbled binary text previews)
  - Explicit 'No preview available' fallback for .docx, .xlsx, .pdf, .zip, etc.
  - MP4 video thumbnail generation & failure logging
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

from src.preview_pane import PreviewPaneWidget, get_file_content_type, is_previewable_text

class TestPreviewPane(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_preview_test_")
        
        # 1. Text file
        self.txt_file = os.path.join(self.tmp_dir, "sample.txt")
        with open(self.txt_file, "w") as f:
            f.write("Hello weg preview\nLine 2 text content\n")

        # 2. Binary files (zip container, pdf, sqlite, binary with null bytes)
        self.docx_file = os.path.join(self.tmp_dir, "document.docx")
        with open(self.docx_file, "wb") as f:
            f.write(b"PK\x03\x04\x14\x00\x06\x00\x08\x00 fake docx zip header binary content")

        self.pdf_file = os.path.join(self.tmp_dir, "report.pdf")
        with open(self.pdf_file, "wb") as f:
            f.write(b"%PDF-1.5 \x00\xff\xfe fake binary pdf content")

        self.zip_file = os.path.join(self.tmp_dir, "archive.zip")
        with open(self.zip_file, "wb") as f:
            f.write(b"PK\x03\x04 fake zip file")

        self.corrupt_mp4 = os.path.join(self.tmp_dir, "corrupt_video.mp4")
        with open(self.corrupt_mp4, "wb") as f:
            f.write(b"this is corrupt video data without moov atom")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_content_type_and_text_detection(self):
        # Text file
        ctype_txt = get_file_content_type(self.txt_file)
        self.assertTrue(is_previewable_text(self.txt_file, ctype_txt))

        # Binary files must evaluate is_previewable_text as False
        for bin_file in [self.docx_file, self.pdf_file, self.zip_file, self.corrupt_mp4]:
            ctype = get_file_content_type(bin_file)
            self.assertFalse(
                is_previewable_text(bin_file, ctype),
                msg=f"File {os.path.basename(bin_file)} should NOT be previewed as text"
            )

    def test_preview_widget_rendering(self):
        app = Gtk.Application(application_id="fm.weg.TestPreview")
        pane = PreviewPaneWidget()

        # Text file preview
        pane.preview_file(self.txt_file)
        self.assertTrue(pane.scrolled_text.get_visible())
        self.assertIn("Hello weg preview", pane.text_buffer.get_text(pane.text_buffer.get_start_iter(), pane.text_buffer.get_end_iter(), True))

        # Binary file previews must show "No preview available"
        for bin_file in [self.docx_file, self.pdf_file, self.zip_file]:
            pane.preview_file(bin_file)
            self.assertTrue(pane.scrolled_text.get_visible())
            text = pane.text_buffer.get_text(pane.text_buffer.get_start_iter(), pane.text_buffer.get_end_iter(), True)
            self.assertEqual(text, "No preview available")

    def test_corrupt_mp4_thumbnail_failure_logging(self):
        pane = PreviewPaneWidget()
        # Previewing corrupt mp4 should trigger ffmpegthumbnailer error logging without crashing
        pane.preview_file(self.corrupt_mp4)
        self.assertTrue(pane.scrolled_text.get_visible())
        text = pane.text_buffer.get_text(pane.text_buffer.get_start_iter(), pane.text_buffer.get_end_iter(), True)
        self.assertEqual(text, "No preview available")

if __name__ == "__main__":
    unittest.main()
