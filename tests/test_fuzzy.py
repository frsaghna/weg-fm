#!/usr/bin/python3
"""
Automated unit verification for Phase 8.4 (Fuzzy Subsequence Matching & Ranking).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fuzzy import fuzzy_match, fuzzy_filter_items
from src.file_list import FileItem

class TestFuzzyMatching(unittest.TestCase):
    def test_fuzzy_match_subsequence(self):
        # Matching subsequence
        matched, score1 = fuzzy_match("wfm", "weg_file_manager.py")
        self.assertTrue(matched)

        # Boundary bonus test: 'wfm' vs 'window_file_menu'
        matched_b, score2 = fuzzy_match("wfm", "window_file_menu")
        self.assertTrue(matched_b)

        # Non-matching subsequence
        matched_fail, _ = fuzzy_match("xyz", "weg_file_manager.py")
        self.assertFalse(matched_fail)

    def test_fuzzy_filter_items(self):
        items = [
            FileItem("weg_file_manager.py", "/p/weg_file_manager.py", False),
            FileItem("window.py", "/p/window.py", False),
            FileItem("file_list.py", "/p/file_list.py", False),
        ]

        # Query 'wfm' should rank 'weg_file_manager.py' first
        filtered = fuzzy_filter_items(items, "wfm", key_fn=lambda i: i.name)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].name, "weg_file_manager.py")

        # Query 'win' should match 'window.py'
        filtered_win = fuzzy_filter_items(items, "win", key_fn=lambda i: i.name)
        self.assertTrue(any(i.name == "window.py" for i in filtered_win))

if __name__ == "__main__":
    unittest.main()
