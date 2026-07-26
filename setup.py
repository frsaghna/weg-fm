from setuptools import setup
import os
import shutil

# Ensure build cache is purged on every setup invocation
if os.path.exists("build"):
    shutil.rmtree("build", ignore_errors=True)

setup(
    name="weg-fm",
    version="1.0.5",
    description="Keyboard-first GTK4 file manager for Linux",
    author="weg-fm contributors",
    license="GPL-3.0-or-later",
    packages=["src"],
    data_files=[
        ("share/applications", ["fm.weg.WegFM.desktop"]),
        ("share/licenses/weg-fm", ["LICENSE"]),
    ],
    entry_points={
        "console_scripts": [
            "weg=src.main:main",
        ],
    },
)
