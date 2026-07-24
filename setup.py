from setuptools import setup, find_packages

setup(
    name="weg-fm",
    version="0.1.0",
    description="A minimal, keyboard-first GTK4/GIO file explorer for Linux",
    author="weg contributors",
    packages=find_packages(),
    py_modules=["weg"],
    entry_points={
        "console_scripts": [
            "weg=src.main:main",
        ],
    },
)
