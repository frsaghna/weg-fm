# weg (`weg-fm`)

Keyboard-first GTK4 file manager for Linux featuring native desktop interop, multi-level atomic undo/redo, frecency navigation, context tabs, customizable themes, and reliability hardening for symlinks and permissions.

---

## Overview

`weg` is a high-performance, keyboard-driven file manager built with GTK4 and Python. Designed for speed, safety, and desktop integration, `weg` combines modal command grammar with full Wayland/X11 clipboard and drag-and-drop interop, zoxide-style frecency jumping, and non-blocking directory scanning.

---

## Key Features

- **Keyboard-First Navigation**: Move through directory structures using Vim-style keys (`h`/`j`/`k`/`l`), jump to list boundaries (`g`/`G`), page jump (`Ctrl+D`/`Ctrl+U`), toggle hidden dotfiles (`.` / `Ctrl+H`), and navigate to `$HOME` (`~`).
- **Full Multi-Level Undo / Redo**: Atomic composite undo/redo stack (`u` / `Ctrl+Z`, `Ctrl+R` / `Ctrl+Y`, `:undo`, `:redo`) covering file moves, copies, batch renames, and trash operations. Batch renames execute via a two-stage temporary path resolution to guarantee 100% atomicity under undo.
- **XDG Trash Restoration**: Trash operations (`x`) move files to XDG Trash via GIO. Undoing a trash action parses `.trashinfo` metadata files to restore items to their original filesystem paths.
- **Browser-Style Directory History**: Independent back and forward history stacks per context tab (`Alt+Left` / `Alt+Right`, `Alt+h` / `Alt+l`, `Ctrl+O` / `Ctrl+I`, `:back`, `:forward`).
- **Frecency Quick Jump (`:z`)**: Jump directly to frequently and recently visited directories using fuzzy fragment queries (`z` key / `:z <fragment>`).
- **Fuzzy Subsequence Search & Live Filter**: Current-directory live filtering (`/`) and recursive `fd`-powered search (`>`) score and rank matches by fuzzy subsequence boundaries.
- **User-Adjustable Preview Pane**: Interactive, draggable split view (`Gtk.Paned`) for side-by-side file previews (`Tab` key). Displays syntax-aware text previews, image viewports, and dynamic video thumbnails via `ffmpegthumbnailer`.
- **Reliability & Symlink Hardening**:
  - Symlinks are deleted via `os.unlink` with `NOFOLLOW_SYMLINKS`, removing only the link pointer and leaving target directories/files untouched.
  - Broken symlinks render with explicit visual indicators (`[broken]`) without raising stat exceptions.
  - Directories with restricted permissions display clear inline error states (`[Permission Denied or Unreadable Directory]`) rather than silently failing.
  - Non-blocking directory enumeration prevents main loop UI freezes in directories containing 50,000+ files.
- **Context Tabs**: 8 independent navigation contexts (`1` through `8`, `:context <1-8>`), each maintaining separate active paths, selections, and history stacks.
- **Native Clipboard & Drag and Drop**: Native GTK/Wayland clipboard interop (`x-special/gnome-copied-files` and `Gdk.FileList`) supporting Cut (`Ctrl+X`), Copy (`Ctrl+C`), and Paste (`Ctrl+V`) to and from external file managers (Nautilus, Dolphin). Drag and drop support for moving/copying files into and out of external windows.
- **Archive Management**: Native creation (`:zip`, `:tar`) and extraction (`:unzip`, `:untar`) of ZIP and TAR archives.
- **Customizable Themes & Icon Sets**: Dynamic theme switching (`:theme <name>`) supporting Catppuccin, Nord, Tokyo Night, Gruvbox, Dracula, and Matrix Green. Icon set selection (`:icon nerdfont|minimal|unicode`). Configurations auto-persist in `~/.config/weg/config.json`.

---

## Command Grammar

`weg` provides three input modes accessible directly from navigation:

| Mode Prefix | Purpose | Example Commands |
|---|---|---|
| `/` | Live filter current directory items using fuzzy matching | `/src`, `/config.json` |
| `>` | Recursive fuzzy search powered by `fd` | `>main.py`, `>test_phase9` |
| `:` | Executive command bar for filesystem and app operations | `:mkdir <dir>`, `:touch <file>`, `:rename <name>`, `:z <fragment>`, `:theme <name>`, `:undo`, `:redo`, `:back`, `:forward` |

---

## Keybindings Reference

### Navigation & Views

| Keybinding | Action |
|---|---|
| `h` / `Left` / `Backspace` | Navigate to parent directory (`..`) |
| `l` / `Right` / `Enter` | Enter selected directory or launch default application for file |
| `k` / `Up` | Move selection up |
| `j` / `Down` | Move selection down |
| `g g` / `Home` | Jump to first item in list |
| `G` / `End` | Jump to last item in list |
| `Ctrl+D` / `Ctrl+U` | Jump down / up half page (10 items) |
| `.` / `Ctrl+H` | Toggle hidden dotfiles visibility |
| `~` | Navigate to `$HOME` directory |
| `Tab` | Toggle user-adjustable side-by-side preview pane |
| `1` - `8` | Switch active context tab |
| `q` | Quit application |

### History, Undo & Frecency

| Keybinding | Action |
|---|---|
| `u` / `Ctrl+Z` | Undo last filesystem operation |
| `Ctrl+R` / `Ctrl+Y` | Redo last undone filesystem operation |
| `Alt+Left` / `Alt+h` / `Ctrl+O` | Go back in directory history |
| `Alt+Right` / `Alt+l` / `Ctrl+I` | Go forward in directory history |
| `z` | Open `:z` prompt for frecency quick jump |

### Selection, Clipboard & Operations

| Keybinding | Action |
|---|---|
| `Space` | Toggle selection check on focused item |
| `Ctrl+C` | Copy selected item(s) to system clipboard |
| `Ctrl+X` | Cut selected item(s) to system clipboard |
| `Ctrl+V` | Paste item(s) from system clipboard |
| `r` | Activate inline rename prompt |
| `x` | Move selected item(s) to Trash |
| `Shift+X` | Permanently delete selected item(s) (with safety confirmation dialog) |
| `Ctrl+L` | Focus location bar for direct path entry |
| `?` / `F1` | Open keybinding help cheat sheet |
| `Esc` | Cancel command bar / live filter and return focus to list view |

---

## Configuration & Themes

`weg` automatically persists settings to `~/.config/weg/config.json`.

Available built-in themes:
- `tokyonight` (default)
- `catppuccin`
- `nord`
- `gruvbox`
- `dracula`
- `matrix`

Switch themes dynamically via command mode:
```text
:theme nord
:theme catppuccin
```

Switch icon sets:
```text
:icon nerdfont
:icon minimal
:icon unicode
```

---

## Installation & Requirements

### System Dependencies

`weg` requires GTK4, PyGObject, and optional CLI utilities for search and thumbnailing:

- Arch Linux:
  ```bash
  sudo pacman -S gtk4 python-gobject fd ffmpegthumbnailer
  ```
- Ubuntu / Debian:
  ```bash
  sudo apt install libgtk-4-dev python3-gi fd-find ffmpegthumbnailer
  ```

### Running Locally

Execute directly from source:
```bash
./weg [directory_path]
```

### Installation

Install as a system or user Python package:
```bash
python3 setup.py install --user
```

---

## Testing

Run the automated test suite (44 unit tests):
```bash
python3 -m unittest discover tests
```

---

## License

MIT License
