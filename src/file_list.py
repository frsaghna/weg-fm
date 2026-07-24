"""
File list widget using GTK4 Gtk.ListBox with multi-select, live filtering (/),
and recursive search (>) support.
"""

import os
import subprocess
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gio', '2.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, Gio, GLib

class FileItem:
    def __init__(self, name, path, is_dir, size=0, display_path=None):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.size = size
        self.display_path = display_path or name

class FileListWidget(Gtk.ScrolledWindow):
    def __init__(self, on_open_directory, on_status_change):
        super().__init__()
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.on_open_directory = on_open_directory
        self.on_status_change = on_status_change
        self.current_dir = ""
        self.all_items = []
        self.displayed_items = []
        self.selected_paths = set()
        self.is_search_mode = False

        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.connect("row-activated", self._on_row_activated)
        self.list_box.connect("row-selected", self._on_row_selected)
        self.set_child(self.list_box)

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
                "standard::name,standard::type,standard::size",
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
            size = info.get_size()
            item_path = os.path.join(path, name)
            new_items.append(FileItem(name, item_path, is_dir, size))
            info = enumerator.next_file(None)

        enumerator.close(None)
        new_items.sort(key=lambda item: (not item.is_dir, item.name.lower()))
        
        self.all_items = new_items
        self._populate_list(self.all_items)
        return True

    def filter_local(self, query):
        if not query:
            self._populate_list(self.all_items)
            return

        query_lower = query.lower()
        filtered = [item for item in self.all_items if query_lower in item.name.lower()]
        self._populate_list(filtered)

    def search_recursive(self, query):
        if not query or not self.current_dir:
            return

        self.is_search_mode = True
        # Use tiered fd search strategy validated in Phase 1c (--max-depth 5 for fast responsive search)
        cmd = ["fd", "--hidden", "--exclude", ".git", "--max-depth", "5", query, self.current_dir]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
            lines = [l for l in res.stdout.splitlines() if l.strip()]
        except Exception as e:
            print(f"[FileList] fd search error: {e}")
            return

        search_items = []
        for p in lines[:200]: # limit to top 200 items for UI responsiveness
            rel_path = os.path.relpath(p, self.current_dir)
            is_dir = os.path.isdir(p)
            size = os.path.getsize(p) if not is_dir and os.path.exists(p) else 0
            search_items.append(FileItem(
                name=os.path.basename(p),
                path=p,
                is_dir=is_dir,
                size=size,
                display_path=rel_path
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
            row_box.set_margin_top(4)
            row_box.set_margin_bottom(4)
            row_box.set_margin_start(8)
            row_box.set_margin_end(8)

            is_selected = item.path in self.selected_paths
            sel_prefix = "[x] " if is_selected else "[ ] "
            dir_prefix = "📁 " if item.is_dir else "   "
            disp = item.display_path if hasattr(item, 'display_path') else item.name
            label_text = f"{sel_prefix}{dir_prefix}{disp}{'/' if item.is_dir else ''}"

            lbl = Gtk.Label(label=label_text, xalign=0.0)
            row_box.append(lbl)

            row = Gtk.ListBoxRow()
            row.set_child(row_box)
            row.item_data = item
            self.list_box.append(row)

        if items:
            first_row = self.list_box.get_row_at_index(0)
            if first_row:
                self.list_box.select_row(first_row)

        self._update_status_bar()

    def toggle_selection_focused(self):
        item = self.get_focused_item()
        if not item:
            return

        if item.path in self.selected_paths:
            self.selected_paths.remove(item.path)
        else:
            self.selected_paths.add(item.path)

        # Re-render current list items to reflect checkbox state
        self._populate_list(self.displayed_items)

    def get_target_files(self):
        """Returns active multi-selection if non-empty, otherwise current hovered/focused item path in a list."""
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
        row = self.list_box.get_selected_row()
        idx = row.get_index() if row else 0
        new_idx = max(0, min(len(self.displayed_items) - 1, idx + delta))
        target_row = self.list_box.get_row_at_index(new_idx)
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
