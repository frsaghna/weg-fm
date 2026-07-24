#!/usr/bin/env /usr/bin/python3
"""
Automated unit & integration verification for Theme Engine & ':theme' Command.
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
from src.theme import get_available_themes, set_theme, get_current_theme

class TestThemeEngine(unittest.TestCase):
    def test_available_themes(self):
        themes = get_available_themes()
        self.assertIn("catppuccin", themes)
        self.assertIn("nord", themes)
        self.assertIn("tokyonight", themes)
        self.assertIn("gruvbox", themes)
        self.assertIn("dracula", themes)
        self.assertIn("matrix", themes)

    def test_set_theme_switching(self):
        ok, msg = set_theme("nord")
        self.assertTrue(ok)
        self.assertEqual(get_current_theme(), "nord")

        ok, msg = set_theme("tokyonight")
        self.assertTrue(ok)
        self.assertEqual(get_current_theme(), "tokyonight")

    def test_theme_command_in_window(self):
        tmp_dir = tempfile.mkdtemp(prefix="weg_theme_test_")
        win = WegWindow(Gtk.Application(application_id="fm.weg.TestTheme"), initial_dir=tmp_dir)

        # Test :theme nord with prefix
        win.execute_command("theme nord")
        self.assertEqual(get_current_theme(), "nord")

        # Test standalone 'theme tokyonight' typed directly into command bar without prefix
        win.command_bar.deactivate()
        win.command_bar.entry.set_text("theme tokyonight")
        win.command_bar._on_activate(win.command_bar.entry)
        self.assertEqual(get_current_theme(), "tokyonight")

        # Test invalid theme name
        win.execute_command("theme invalid_name")
        self.assertIn("Unknown theme", win.status_bar.get_text())

        import shutil
        shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    unittest.main()
