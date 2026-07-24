"""
File list widget using GTK4 Gtk.ListBox with Neovim / LazyVim ergonomics:
  - Customizable iconsets ('nerdfont', 'minimal', 'unicode')
  - Minimalist monochrome Nerd Font glyphs (default)
  - Neovim cursorline highlighting
  - Half-page jumping (Ctrl+D / Ctrl+U)
  - Hidden files toggle (.)
"""

import os
import shutil
import subprocess
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gio', '2.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, Gio, GLib

# Icon Sets
ICON_SETS = {
    "nerdfont": {
        "dir": "󰉋",
        "exec": "󰜎",
        "python": "",
        "doc": "󰍔",
        "config": "󰅩",
        "image": "󰋩",
        "archive": "",
        "script": "",
        "code": "",
        "file": "󰈔",
    },
    "minimal": {
        "dir": "▸",
        "exec": "*",
        "python": "·",
        "doc": "·",
        "config": "·",
        "image": "·",
        "archive": "·",
        "script": "·",
        "code": "·",
        "file": "·",
    },
    "unicode": {
        "dir": "📁",
        "exec": "⚡",
        "python": "🐍",
        "doc": "📝",
        "config": "⚙️",
        "image": "🖼️",
        "archive": "📦",
        "script": "📜",
        "code": "💻",
        "file": "📄",
    }
}

class FileItem:
    def __init__(self, name, path, is_dir, size=0, display_path=None, is_exec=False, iconset="nerdfont"):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.size = size
        self.display_path = display_path or name
        self.is_exec = is_exec
        self.icon = self._resolve_icon(iconset)

    def _resolve_icon(self, iconset_name):
        palette = ICON_SETS.get(iconset_name, ICON_SETS["nerdfont"])
        if self.is_dir:
            return palette["dir"]

        ext = os.path.splitext(self.name)[1].lower()

        # Check extension first so script/source icons take priority over generic exec permission
        if ext in ('.sh', '.bash', '.zsh', '.fish'):
            return palette["script"]
        elif ext in ('.py', '.pyw'):
            return palette["python"]
        elif ext in ('.md', '.markdown', '.txt', '.doc', '.docx', '.pdf'):
            return palette["doc"]
        elif ext in ('.json', '.yaml', '.yml', '.toml', '.edn', '.ini', '.conf'):
            return palette["config"]
        elif ext in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp'):
            return palette["image"]
        elif ext in ('.zip', '.tar', '.gz', '.bz2', '.7z', '.xz', '.rar'):
            return palette["archive"]
        elif ext in ('.rs', '.c', '.cpp', '.h', '.go', '.js', '.ts', '.html', '.css'):
            return palette["code"]
        elif self.is_exec:
            return palette["exec"]

        return palette["file"]

class FileListWidget(Gtk.ScrolledWindow):
    def __init__(self, on_open_directory, on_status_change):
        super().__init__()
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.on_open_directory = on_open_directory
        self.on_status_change = on_status_change
        self.current_dir = ""
        self.show_hidden = False
        self.iconset = "nerdfont"
        self.all_items = []
        self.displayed_items = []
        self.selected_paths = set()
        self.is_search_mode = False

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.connect("row-activated", self._on_row_activated)
        self.list_box.connect("row-selected", self._on_row_selected)
        self.set_child(self.list_box)

        # Setup Gtk.DropTarget
        drop_target = Gtk.DropTarget.new(
            type=Gdk.FileList,
            actions=Gdk.DragAction.COPY | Gdk.DragAction.MOVE
        )
        drop_target.connect("enter", self._on_drop_enter)
        drop_target.connect("drop", self._on_drop)
        self.add_controller(drop_target)

    def set_iconset(self, name):
        if name in ICON_SETS:
            self.iconset = name
            if self.current_dir:
                self.load_directory(self.current_dir)
            return True, f"Icon set changed to '{name}'"
        return False, f"Unknown icon set '{name}'. Available: {', '.join(ICON_SETS.keys())}"

    def toggle_hidden_files(self):
        self.show_hidden = not self.show_hidden
        self._apply_current_filter()
        if self.on_status_change:
            self.on_status_change(f"Hidden dotfiles {'shown' if self.show_hidden else 'hidden'}")

    def _on_drop_enter(self, target, x, y):
        return Gdk.DragAction.COPY | Gdk.DragAction.MOVE

    def _on_drop(self, target, value, x, y):
        if not self.current_dir or not os.path.exists(self.current_dir):
            return False

        dropped_files = []
        if isinstance(value, Gdk.FileList):
            dropped_files = [f.get_path() for f in value.get_files() if f.get_path()]
        elif hasattr(value, "get_files"):
            dropped_files = [f.get_path() for f in value.get_files() if f.get_path()]

        if not dropped_files:
            return False

        for src_path in dropped_files:
            if not os.path.exists(src_path):
                continue
            dest_name = os.path.basename(src_path)
            dest_path = os.path.join(self.current_dir, dest_name)
            if src_path == dest_path:
                continue
            
            try:
                if os.path.isdir(src_path):
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path, ignore_errors=True)
                    shutil.copytree(src_path, dest_path)
                else:
                    shutil.copy2(src_path, dest_path)
            except Exception as e:
                print(f"[FileList] Drop copy error for {src_path}: {e}")

        self.load_directory(self.current_dir)
        return True

    def load_directory(self, path):
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            return False

        self.current_dir = path
        self.selected_paths.clear()
        self.is_search_mode = False
        gfile = Gio.File.new_for_path(path)

        try:
            enumerator = gfile.enumerate_children(
                "standard::name,standard::type,standard::size,access::can-execute",
                Gio.FileQueryInfoFlags.NONE,
                None
            )
        except Exception as e:
            print(f"[FileList] Error opening directory {path}: {e}")
            return False

        new_items = []
        info = enumerator.next_file(None)
        while info:
            name = info.get_name()
            ftype = info.get_file_type()
            is_dir = (ftype == Gio.FileType.DIRECTORY)
            is_exec = info.get_attribute_boolean("access::can-execute") if not is_dir else False
            size = info.get_size()
            item_path = os.path.join(path, name)
            new_items.append(FileItem(name, item_path, is_dir, size, is_exec=is_exec, iconset=self.iconset))
            info = enumerator.next_file(None)

        enumerator.close(None)
        new_items.sort(key=lambda item: (not item.is_dir, item.name.lower()))
        
        self.all_items = new_items
        self._apply_current_filter()
        return True

    def _apply_current_filter(self):
        filtered = self.all_items
        if not self.show_hidden:
            filtered = [item for item in filtered if not item.name.startswith('.')]
        self._populate_list(filtered)

    def filter_local(self, query):
        if not query:
            self._apply_current_filter()
            return

        query_lower = query.lower()
        filtered = self.all_items
        if not self.show_hidden:
            filtered = [item for item in filtered if not item.name.startswith('.')]
        filtered = [item for item in filtered if query_lower in item.name.lower()]
        self._populate_list(filtered)

    def search_recursive(self, query):
        if not query or not self.current_dir:
            return

        self.is_search_mode = True
        cmd = ["fd", "--exclude", ".git", "--max-depth", "5", query, self.current_dir]
        if self.show_hidden:
            cmd.insert(1, "--hidden")
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
            lines = [l for l in res.stdout.splitlines() if l.strip()]
        except Exception as e:
            print(f"[FileList] fd search error: {e}")
            return

        search_items = []
        for p in lines[:200]:
            rel_path = os.path.relpath(p, self.current_dir)
            is_dir = os.path.isdir(p)
            is_exec = os.access(p, os.X_OK) if not is_dir and os.path.exists(p) else False
            size = os.path.getsize(p) if not is_dir and os.path.exists(p) else 0
            search_items.append(FileItem(
                name=os.path.basename(p),
                path=p,
                is_dir=is_dir,
                size=size,
                display_path=rel_path,
                is_exec=is_exec,
                iconset=self.iconset
            ))

        search_items.sort(key=lambda item: (not item.is_dir, item.display_path.lower()))
        self._populate_list(search_items)

    def _populate_list(self, items):
        self.displayed_items = items
        while True:
            row = self.list_box.get_row_at_index(0)
            if row is None:
                break
            self.list_box.remove(row)

        for item in items:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row_box.set_margin_top(3)
            row_box.set_margin_bottom(3)
            row_box.set_margin_start(8)
            row_box.set_margin_end(8)

            is_selected = item.path in self.selected_paths
            sel_text = "[x] " if is_selected else "[ ] "
            sel_label = Gtk.Label(label=sel_text)
            if is_selected:
                sel_label.add_css_class("selected-checkbox")
            row_box.append(sel_label)

            disp = item.display_path if hasattr(item, 'display_path') else item.name
            label_text = f"{item.icon}  {disp}{'/' if item.is_dir else ''}"

            lbl = Gtk.Label(label=label_text, xalign=0.0)
            if item.name.startswith('.'):
                lbl.add_css_class("hidden-item")
            elif item.is_dir:
                lbl.add_css_class("dir-item")
            elif item.is_exec:
                lbl.add_css_class("exec-item")
            else:
                lbl.add_css_class("file-item")

            row_box.append(lbl)

            row = Gtk.ListBoxRow()
            row.set_child(row_box)
            row.item_data = item

            drag_source = Gtk.DragSource.new()
            drag_source.set_actions(Gdk.DragAction.COPY | Gdk.DragAction.MOVE)
            drag_source.connect("prepare", self._on_drag_prepare, item)
            row.add_controller(drag_source)

            self.list_box.append(row)

        if items:
            first_row = self.list_box.get_row_at_index(0)
            if first_row:
                self.list_box.select_row(first_row)

        self._update_status_bar()

    def _on_drag_prepare(self, source, x, y, item):
        target_paths = self.get_target_files()
        if item.path not in target_paths:
            target_paths = [item.path]

        gfiles = [Gio.File.new_for_path(p) for p in target_paths]
        file_list = Gdk.FileList.new_from_list(gfiles)
        return Gdk.ContentProvider.new_for_value(file_list)

    def toggle_selection_focused(self):
        item = self.get_focused_item()
        if not item:
            return

        if item.path in self.selected_paths:
            self.selected_paths.remove(item.path)
        else:
            self.selected_paths.add(item.path)

        self._populate_list(self.displayed_items)

    def get_target_files(self):
        if self.selected_paths:
            return list(self.selected_paths)
        focused = self.get_focused_item()
        if focused:
            return [focused.path]
        return []

    def get_focused_item(self):
        row = self.list_box.get_selected_row()
        if row and hasattr(row, 'item_data'):
            return row.item_data
        return None

    def move_selection(self, delta):
        if not self.displayed_items:
            return
        row = self.list_box.get_selected_row()
        idx = row.get_index() if row else 0
        new_idx = max(0, min(len(self.displayed_items) - 1, idx + delta))
        target_row = self.list_box.get_row_at_index(new_idx)
        if target_row:
            self.list_box.select_row(target_row)
            target_row.grab_focus()

    def jump_half_page(self, direction):
        self.move_selection(direction * 10)

    def jump_to_first(self):
        if self.displayed_items:
            target_row = self.list_box.get_row_at_index(0)
            if target_row:
                self.list_box.select_row(target_row)
                target_row.grab_focus()

    def jump_to_last(self):
        if self.displayed_items:
            target_row = self.list_box.get_row_at_index(len(self.displayed_items) - 1)
            if target_row:
                self.list_box.select_row(target_row)
                target_row.grab_focus()

    def activate_selected(self):
        item = self.get_focused_item()
        if not item:
            return

        if item.is_dir:
            self.on_open_directory(item.path)
        else:
            gfile = Gio.File.new_for_path(item.path)
            Gio.AppInfo.launch_default_for_uri_async(gfile.get_uri(), None, None, None)

    def _on_row_activated(self, list_box, row):
        if hasattr(row, 'item_data'):
            item = row.item_data
            if item.is_dir:
                self.on_open_directory(item.path)
            else:
                gfile = Gio.File.new_for_path(item.path)
                Gio.AppInfo.launch_default_for_uri_async(gfile.get_uri(), None, None, None)

    def _on_row_selected(self, list_box, row):
        self._update_status_bar()

    def _update_status_bar(self):
        if not self.on_status_change:
            return

        num_sel = len(self.selected_paths)
        if num_sel > 0:
            self.on_status_change(f"{num_sel} item(s) selected ({len(self.displayed_items)} shown)")
        else:
            focused = self.get_focused_item()
            if focused:
                size_str = f" ({focused.size} bytes)" if not focused.is_dir else ""
                self.on_status_change(f"{focused.name}{size_str} — {len(self.displayed_items)} item(s)")
            else:
                self.on_status_change(f"{len(self.displayed_items)} item(s)")
