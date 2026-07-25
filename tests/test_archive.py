#!/usr/bin/python3
"""
Automated unit verification for Zip/Tar Compression and Extraction.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.archive_utils import create_zip_archive, create_tar_archive, extract_archive

class TestArchiveUtils(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="weg_archive_test_")
        self.file1 = os.path.join(self.tmp_dir, "sample.txt")
        with open(self.file1, "w") as f:
            f.write("hello archive")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp_dir)

    def test_zip_create_and_extract(self):
        zip_out = os.path.join(self.tmp_dir, "test_out.zip")
        res = create_zip_archive([self.file1], zip_out)
        self.assertTrue(os.path.exists(res))

        dest_dir = os.path.join(self.tmp_dir, "unzipped")
        os.makedirs(dest_dir)
        ok, msg = extract_archive(res, dest_dir)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(os.path.join(dest_dir, "sample.txt")))

    def test_tar_create_and_extract(self):
        tar_out = os.path.join(self.tmp_dir, "test_out.tar.gz")
        res = create_tar_archive([self.file1], tar_out)
        self.assertTrue(os.path.exists(res))

        dest_dir = os.path.join(self.tmp_dir, "untarred")
        os.makedirs(dest_dir)
        ok, msg = extract_archive(res, dest_dir)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(os.path.join(dest_dir, "sample.txt")))

if __name__ == "__main__":
    unittest.main()
