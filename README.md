# weg (`weg-fm`)

*Minimal, keyboard-first GTK4 file explorer for Linux with native desktop interop, `nnn` ergonomics, and customizable TUI themes.*

---

## 🌟 Key Features

- **`nnn`-Exact Keyboard Ergonomics**: Move through directories instantly using `h`/`l`/`j`/`k` or arrow keys, jump top/bottom with `g`/`G`, toggle dotfiles with `.`, navigate to `$HOME` with `~`, and quit with `q`.
- **Customizable TUI Themes**: Switch themes dynamically via `:theme <name>`. Includes **Catppuccin**, **Nord**, **Tokyo Night**, **Gruvbox**, **Dracula**, and **Matrix Hacker Green**. Preferences auto-persist in `~/.config/weg/config.json`.
- **Command-Line Grammar**:
  - `/query` — Instant current-directory live filter.
  - `>query` — Instant recursive search powered by `fd` (<15ms response).
  - `:command` — Integrated command mode (`:mkdir`, `:touch`, `:rename`, `:delete`, `:theme`, shell).
- **Native Clipboard Interop**: Real file objects on GTK/Wayland clipboard (`x-special/gnome-copied-files` and `Gdk.FileList`). Cut (`Ctrl+X`), Copy (`Ctrl+C`), and Paste (`Ctrl+V`) directly to and from Nautilus, Dolphin, or other GTK/Qt applications.
- **Native Drag and Drop**: Drag files out from `weg` into Nautilus or drag files in from Nautilus (`GtkDragSource` & `GtkDropTarget` supporting `COPY | MOVE` negotiation).
- **Live Directory Updates**: Powered by GIO `GFileMonitor` (inotify-backed) — directory listings update automatically when files change externally.
- **Inline Preview Pane**: Press `Tab` to toggle live side-by-side preview of text files or image/media thumbnails (Freedesktop Thumbnailer spec & GdkPixbuf).
- **Data Safety Policies**: `x` moves items safely to Trash (XDG Trash spec via GIO). `Shift+X` triggers permanent delete with confirmation dialog.

---

## 🎨 Themes & Configuration

Type `:theme` in `weg` to list themes or switch themes live:
```
:theme nord
:theme tokyonight
:theme gruvbox
:theme dracula
:theme matrix
:theme catppuccin
```

Config file location: `~/.config/weg/config.json`

---

## ⌨️ `nnn` Keybindings Reference

| Key | Action |
|---|---|
| `h` / `Left` / `Backspace` | Navigate to parent directory (`..`) |
| `l` / `Right` / `Enter` | Enter selected directory or open file |
| `k` / `Up` | Move selection up |
| `j` / `Down` | Move selection down |
| `g` / `Home` | Jump to first item in list |
| `G` / `End` | Jump to last item in list |
| `.` / `Ctrl+H` | Toggle hidden dotfiles |
| `~` | Go to `$HOME` directory |
| `q` | Quit `weg` |
| `Space` | Toggle multi-selection on focused item |
| `/` | Instant current-directory filter mode |
| `>` | Recursive search mode via `fd` |
| `:` | Command mode (`:mkdir`, `:touch`, `:rename`, `:delete`, `:theme <name>`) |
| `r` | Quick inline rename mode |
| `Ctrl+C` | Copy selected file(s) to clipboard |
| `Ctrl+X` | Cut selected file(s) to clipboard |
| `Ctrl+V` | Paste file(s) from clipboard |
| `Ctrl+L` | Focus path bar for direct path editing |
| `Tab` | Toggle side-by-side file preview pane |
| `x` | Move selected file(s) to Trash (GIO Trash API) |
| `Shift+X` | Permanently delete selected file(s) (with safety confirmation) |
| `?` / `F1` | Open interactive keybinding cheat sheet |
| `Esc` | Clear filter / search / command bar and return to navigation |

---

## 🚀 Installation & Usage

### Dependencies
Ensure system GTK4 and PyGObject dependencies are installed:
- Arch Linux: `pacman -S gtk4 python-gobject fd ffmpegthumbnailer evince`

### Launch Locally
```bash
./weg [directory_path]
```

### Install Package
```bash
python3 setup.py build
```

---

## 🧪 Testing

Run the full automated test suite (16 tests):
```bash
python3 -m unittest discover tests
```

---

## 📜 License
MIT License
