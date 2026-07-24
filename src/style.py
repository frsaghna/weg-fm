"""
TUI Design System & GTK4 CSS styling for weg.
Gives GTK4 a clean, dark, high-contrast monospace Terminal UI (TUI) aesthetic.
"""

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk

TUI_CSS = """
/* Reset & Global Monospace Typography */
* {
    font-family: 'JetBrains Mono', 'Fira Code', 'Hack', 'Cascadia Code', 'Liberation Mono', 'monospace';
    font-size: 13px;
    border-radius: 0px;
    box-shadow: none;
    text-shadow: none;
}

/* Main Window Background */
window {
    background-color: #181825;
    color: #cdd6f4;
}

/* Header & Path Bar */
.path-bar {
    background-color: #11111b;
    padding: 6px 12px;
    border-bottom: 1px solid #313244;
}

.path-label {
    color: #89b4fa;
    font-weight: bold;
}

/* Entry Fields (Path Bar & Command Bar) */
entry {
    background-color: #1e1e2e;
    color: #a6e3a1;
    border: 1px solid #45475a;
    padding: 4px 8px;
    caret-color: #f5e0dc;
}

entry:focus {
    border-color: #89b4fa;
    background-color: #181825;
}

/* File List Box & Scrolled Window */
scrolledwindow {
    background-color: #181825;
    border: none;
}

list {
    background-color: #181825;
    color: #cdd6f4;
}

row {
    padding: 4px 10px;
    background-color: transparent;
    color: #cdd6f4;
    border-left: 3px solid transparent;
}

row:hover {
    background-color: #1e1e2e;
}

row:selected {
    background-color: #313244;
    color: #ffffff;
    border-left: 3px solid #89b4fa;
    font-weight: bold;
}

/* File List Directory Items */
.dir-item {
    color: #89b4fa;
    font-weight: bold;
}

.file-item {
    color: #cdd6f4;
}

.exec-item {
    color: #a6e3a1;
    font-weight: bold;
}

.selected-checkbox {
    color: #f9e2af;
    font-weight: bold;
}

/* Separator Lines */
separator {
    background-color: #313244;
    min-height: 1px;
    min-width: 1px;
}

/* Preview Pane */
.preview-pane {
    background-color: #11111b;
    border-left: 1px solid #313244;
    padding: 8px;
}

textview text {
    background-color: #11111b;
    color: #bac2de;
}

/* Status Bar & Command Bar */
.status-bar {
    background-color: #11111b;
    color: #a6adc8;
    padding: 4px 12px;
    border-top: 1px solid #313244;
    font-size: 12px;
}

.mode-badge {
    background-color: #89b4fa;
    color: #11111b;
    font-weight: bold;
    padding: 2px 8px;
    margin-right: 8px;
}

.mode-badge-filter {
    background-color: #a6e3a1;
    color: #11111b;
}

.mode-badge-search {
    background-color: #f9e2af;
    color: #11111b;
}

.mode-badge-cmd {
    background-color: #f38ba8;
    color: #11111b;
}
"""

def apply_tui_theme():
    css_provider = Gtk.CssProvider()
    if hasattr(css_provider, "load_from_string"):
        css_provider.load_from_string(TUI_CSS)
    else:
        css_provider.load_from_data(TUI_CSS.encode('utf-8'))
    display = Gdk.Display.get_default()
    if display:
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
