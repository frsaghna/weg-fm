"""
Theme Engine & Config Manager for weg.
Supports theme switching via ':theme <name>' command and persistence in ~/.config/weg/config.json.
Ultra-compact terminal TUI styling for all entry fields, status bars, and command lines.
"""

import os
import json
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk

CONFIG_DIR = os.path.expanduser("~/.config/weg")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

THEMES = {
    "catppuccin": {
        "name": "Catppuccin Mocha",
        "bg": "#181825",
        "fg": "#cdd6f4",
        "header_bg": "#11111b",
        "dir_color": "#89b4fa",
        "file_color": "#cdd6f4",
        "exec_color": "#a6e3a1",
        "selection_bg": "#313244",
        "selection_accent": "#89b4fa",
        "border_color": "#313244",
        "entry_bg": "#1e1e2e",
        "entry_fg": "#a6e3a1",
        "entry_border": "#45475a",
        "card_bg": "#1e1e2e",
        "badge_bg": "#89b4fa",
        "badge_fg": "#11111b",
        "badge_filter": "#a6e3a1",
        "badge_search": "#f9e2af",
        "badge_cmd": "#f38ba8",
    },
    "nord": {
        "name": "Nord Arctic",
        "bg": "#2e3440",
        "fg": "#eceff4",
        "header_bg": "#242933",
        "dir_color": "#88c0d0",
        "file_color": "#e5e9f0",
        "exec_color": "#a3be8c",
        "selection_bg": "#3b4252",
        "selection_accent": "#81a1c1",
        "border_color": "#434c5e",
        "entry_bg": "#3b4252",
        "entry_fg": "#a3be8c",
        "entry_border": "#4c566a",
        "card_bg": "#3b4252",
        "badge_bg": "#88c0d0",
        "badge_fg": "#2e3440",
        "badge_filter": "#a3be8c",
        "badge_search": "#ebcb8b",
        "badge_cmd": "#bf616a",
    },
    "tokyonight": {
        "name": "Tokyo Night",
        "bg": "#1a1b26",
        "fg": "#a9b1d6",
        "header_bg": "#16161e",
        "dir_color": "#7aa2f7",
        "file_color": "#c0caf5",
        "exec_color": "#9ece6a",
        "selection_bg": "#283457",
        "selection_accent": "#7dcfff",
        "border_color": "#292e42",
        "entry_bg": "#24283b",
        "entry_fg": "#73daca",
        "entry_border": "#414868",
        "card_bg": "#24283b",
        "badge_bg": "#7aa2f7",
        "badge_fg": "#15161e",
        "badge_filter": "#9ece6a",
        "badge_search": "#e0af68",
        "badge_cmd": "#bb9af7",
    },
    "gruvbox": {
        "name": "Gruvbox Dark",
        "bg": "#282828",
        "fg": "#ebdbb2",
        "header_bg": "#1d2021",
        "dir_color": "#83a598",
        "file_color": "#fbf1c7",
        "exec_color": "#b8bb26",
        "selection_bg": "#3c3836",
        "selection_accent": "#fabd2f",
        "border_color": "#504945",
        "entry_bg": "#3c3836",
        "entry_fg": "#b8bb26",
        "entry_border": "#665c54",
        "card_bg": "#3c3836",
        "badge_bg": "#fabd2f",
        "badge_fg": "#282828",
        "badge_filter": "#b8bb26",
        "badge_search": "#fe8019",
        "badge_cmd": "#fb4934",
    },
    "dracula": {
        "name": "Dracula",
        "bg": "#282a36",
        "fg": "#f8f8f2",
        "header_bg": "#21222c",
        "dir_color": "#8be9fd",
        "file_color": "#f8f8f2",
        "exec_color": "#50fa7b",
        "selection_bg": "#44475a",
        "selection_accent": "#bd93f9",
        "border_color": "#6272a4",
        "entry_bg": "#44475a",
        "entry_fg": "#50fa7b",
        "entry_border": "#6272a4",
        "card_bg": "#44475a",
        "badge_bg": "#bd93f9",
        "badge_fg": "#282a36",
        "badge_filter": "#50fa7b",
        "badge_search": "#f1fa8c",
        "badge_cmd": "#ff5555",
    },
    "matrix": {
        "name": "Matrix Hacker Green",
        "bg": "#0d0d0d",
        "fg": "#00ff66",
        "header_bg": "#050505",
        "dir_color": "#00ffff",
        "file_color": "#00ff66",
        "exec_color": "#33ff33",
        "selection_bg": "#003311",
        "selection_accent": "#00ff66",
        "border_color": "#00441b",
        "entry_bg": "#001a08",
        "entry_fg": "#00ff66",
        "entry_border": "#006622",
        "card_bg": "#001a08",
        "badge_bg": "#00ff66",
        "badge_fg": "#000000",
        "badge_filter": "#00ffff",
        "badge_search": "#ffff00",
        "badge_cmd": "#ff0055",
    }
}

_css_provider = None
_current_theme = "tokyonight"

def generate_theme_css(palette):
    return f"""
/* Terminal Global Font Reset */
* {{
    font-family: 'JetBrains Mono', 'Fira Code', 'Hack', 'Cascadia Code', 'Liberation Mono', 'monospace';
    font-size: 12px;
    border-radius: 0px;
    box-shadow: none;
    text-shadow: none;
    margin: 0px;
}}

window {{
    background-color: {palette['bg']};
    color: {palette['fg']};
}}

/* Ultra-Compact Path Bar / Bufferline */
.path-bar {{
    background-color: {palette['header_bg']};
    padding: 2px 8px;
    min-height: 22px;
    border-bottom: 1px solid {palette['border_color']};
}}

.path-label {{
    color: {palette['dir_color']};
    font-weight: bold;
    font-size: 12px;
}}

/* Ultra-Compact Entry Fields (Terminal Commandline & Path Editing) */
entry {{
    background-color: {palette['header_bg']};
    color: {palette['entry_fg']};
    border: none;
    padding: 1px 4px;
    min-height: 20px;
    font-size: 12px;
}}

entry:focus {{
    background-color: {palette['bg']};
    color: {palette['entry_fg']};
    border: none;
}}

/* List View & Row Spacing (Neovim cursorline style) */
scrolledwindow {{
    background-color: {palette['bg']};
    border: none;
}}

list {{
    background-color: {palette['bg']};
    color: {palette['fg']};
}}

row {{
    padding: 2px 8px;
    min-height: 20px;
    background-color: transparent;
    color: {palette['fg']};
    border-left: 2px solid transparent;
}}

row:hover {{
    background-color: {palette['entry_bg']};
}}

row:selected {{
    background-color: {palette['selection_bg']};
    color: #ffffff;
    border-left: 2px solid {palette['selection_accent']};
    font-weight: bold;
}}

.dir-item {{
    color: {palette['dir_color']};
    font-weight: bold;
}}

.file-item {{
    color: {palette['file_color']};
}}

.hidden-item {{
    color: #565f89;
}}

.exec-item {{
    color: {palette['exec_color']};
    font-weight: bold;
}}

.selected-checkbox {{
    color: {palette['badge_search']};
    font-weight: bold;
}}

separator {{
    background-color: {palette['border_color']};
    min-height: 1px;
    min-width: 1px;
}}

/* Preview Pane */
.preview-pane {{
    background-color: {palette['header_bg']};
    border-left: 1px solid {palette['border_color']};
    padding: 6px;
}}

textview text {{
    background-color: {palette['header_bg']};
    color: {palette['fg']};
}}

/* Ultra-Compact Status & Command Bars (Neovim Lualine style) */
.status-bar {{
    background-color: {palette['header_bg']};
    color: {palette['fg']};
    padding: 2px 8px;
    min-height: 20px;
    border-top: 1px solid {palette['border_color']};
    font-size: 11px;
}}

.mode-badge {{
    background-color: {palette['badge_bg']};
    color: {palette['badge_fg']};
    font-weight: bold;
    padding: 1px 6px;
    min-height: 18px;
    margin-right: 4px;
    font-size: 11px;
}}

.mode-badge-filter {{
    background-color: {palette['badge_filter']};
    color: {palette['badge_fg']};
}}

.mode-badge-search {{
    background-color: {palette['badge_search']};
    color: {palette['badge_fg']};
}}

.mode-badge-cmd {{
    background-color: {palette['badge_cmd']};
    color: {palette['badge_fg']};
}}

.help-card {{
    background-color: {palette['card_bg']};
    border: 1px solid {palette['border_color']};
    padding: 10px;
    margin-bottom: 8px;
}}

.help-title {{
    color: {palette['badge_search']};
    font-weight: bold;
    font-size: 12px;
    margin-bottom: 6px;
}}

.key-cap {{
    background-color: {palette['selection_bg']};
    color: {palette['exec_color']};
    border: 1px solid {palette['entry_border']};
    font-weight: bold;
    padding: 1px 5px;
    border-radius: 2px;
    font-size: 11px;
}}

.key-desc {{
    color: {palette['fg']};
    font-size: 12px;
}}
"""

def get_available_themes():
    return list(THEMES.keys())

def get_current_theme():
    return _current_theme

def set_theme(theme_name):
    global _css_provider, _current_theme
    theme_key = theme_name.lower().strip()
    if theme_key not in THEMES:
        return False, f"Unknown theme '{theme_name}'. Available: {', '.join(get_available_themes())}"

    _current_theme = theme_key
    palette = THEMES[theme_key]
    css_data = generate_theme_css(palette)

    display = Gdk.Display.get_default()
    if display:
        if _css_provider is None:
            _css_provider = Gtk.CssProvider()
            Gtk.StyleContext.add_provider_for_display(
                display,
                _css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        
        if hasattr(_css_provider, "load_from_string"):
            _css_provider.load_from_string(css_data)
        else:
            _css_provider.load_from_data(css_data.encode('utf-8'))

    save_config({"theme": _current_theme})
    return True, f"Theme set to '{palette['name']}'"

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(config_data):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        current = load_config()
        current.update(config_data)
        with open(CONFIG_PATH, "w") as f:
            json.dump(current, f, indent=2)
    except Exception as e:
        print(f"[Theme] Failed to save config: {e}")

def init_theme():
    config = load_config()
    saved_theme = config.get("theme", "tokyonight")
    set_theme(saved_theme)
