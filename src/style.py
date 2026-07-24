"""
Forwarding style manager for weg.
Connects with theme engine in src/theme.py.
"""

from src.theme import init_theme, set_theme, get_available_themes, get_current_theme

def apply_tui_theme():
    init_theme()
