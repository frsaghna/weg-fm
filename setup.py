from setuptools import setup, find_packages

setup(
    name="weg-fm",
    version="1.0.0",
    description="Keyboard-first GTK4 file manager for Linux",
    author="weg-fm contributors",
    license="GPL-3.0-or-later",
    package_dir={"": "."},
    packages=["weg_fm"],
    data_files=[
        ("share/applications", ["fm.weg.WegFM.desktop"]),
        ("share/licenses/weg-fm", ["LICENSE"]),
    ],
    entry_points={
        "console_scripts": [
            "weg=weg_fm.main:main",
        ],
    },
)
