"""
LazyVim / Neovim Design System & GTK4 CSS styling for weg.
Features TokyoNight Storm palette, bufferline topbar, lualine statusbar segments,
and which-key floating dialog styling.
"""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk

LAZYVIM_CSS = """
/* Reset & Monospace Font Family (Neovim style) */
* {
    font-family: 'JetBrains Mono', 'Fira Code', 'Hack', 'Cascadia Code', 'Liberation Mono', 'monospace';
    font-size: 13px;
    border-radius: 0px;
    box-shadow: none;
    text-shadow: none;
}

/* Main Window Background - TokyoNight Storm */
window {
    background-color: #1a1b26;
    color: #a9b1d6;
}

/* Neovim Top Bufferline / Path Bar */
.path-bar {
    background-color: #16161e;
    padding: 6px 12px;
    border-bottom: 1px solid #292e42;
}

.path-badge {
    background-color: #7aa2f7;
    color: #15161e;
    font-weight: bold;
    padding: 2px 8px;
    margin-right: 8px;
}

.path-label {
    color: #7dcfff;
    font-weight: bold;
}

/* Entry Fields (Cmdline & Path) */
entry {
    background-color: #16161e;
    color: #73daca;
    border: 1px solid #3b4261;
    padding: 4px 8px;
    caret-color: #c0caf5;
}

entry:focus {
    border-color: #7aa2f7;
    background-color: #1a1b26;
}

/* File List & Cursorline Styling (nvim-tree / neo-tree style) */
scrolledwindow {
    background-color: #1a1b26;
    border: none;
}

list {
    background-color: #1a1b26;
    color: #a9b1d6;
}

row {
    padding: 5px 12px;
    background-color: transparent;
    color: #a9b1d6;
    border-left: 3px solid transparent;
}

row:hover {
    background-color: #24283b;
}

row:selected {
    background-color: #2e3c64;
    color: #ffffff;
    border-left: 3px solid #7aa2f7;
    font-weight: bold;
}

/* Filetype Color Coding */
.dir-item {
    color: #7aa2f7;
    font-weight: bold;
}

.file-item {
    color: #c0caf5;
}

.hidden-item {
    color: #565f89;
}

.exec-item {
    color: #9ece6a;
    font-weight: bold;
}

.selected-checkbox {
    color: #e0af68;
    font-weight: bold;
}

/* Separator Lines */
separator {
    background-color: #292e42;
    min-height: 1px;
    min-width: 1px;
}

/* Preview Pane (nvim vertical split style) */
.preview-pane {
    background-color: #16161e;
    border-left: 1px solid #292e42;
    padding: 10px;
}

textview text {
    background-color: #16161e;
    color: #a9b1d6;
}

/* Neovim Lualine Statusbar Segments */
.status-bar {
    background-color: #16161e;
    color: #a9b1d6;
    padding: 4px 12px;
    border-top: 1px solid #292e42;
    font-size: 12px;
}

/* Lualine Mode Badges */
.mode-badge {
    background-color: #7aa2f7;
    color: #15161e;
    font-weight: bold;
    padding: 3px 10px;
    margin-right: 8px;
}

.mode-badge-filter {
    background-color: #9ece6a;
    color: #15161e;
}

.mode-badge-search {
    background-color: #e0af68;
    color: #15161e;
}

.mode-badge-cmd {
    background-color: #bb9af7;
    color: #15161e;
}

/* Which-Key / Telescope Floating Window Styling */
.help-card {
    background-color: #1f2335;
    border: 1px solid #3b4261;
    padding: 12px;
    margin-bottom: 12px;
}

.help-title {
    color: #7dcfff;
    font-weight: bold;
    font-size: 13px;
    margin-bottom: 8px;
}

.key-cap {
    background-color: #292e42;
    color: #73daca;
    border: 1px solid #3b4261;
    font-weight: bold;
    padding: 2px 8px;
    border-radius: 2px;
}

.key-desc {
    color: #c0caf5;
}
"""

def apply_tui_theme():
    css_provider = Gtk.CssProvider()
    if hasattr(css_provider, "load_from_string"):
        css_provider.load_from_string(LAZYVIM_CSS)
    else:
        css_provider.load_from_data(LAZYVIM_CSS.encode('utf-8'))
    display = Gdk.Display.get_default()
    if display:
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
