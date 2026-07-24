"""
File list widget using GTK4 Gtk.ListBox and GIO directory enumeration.
"""

import os
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gio', '2.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Gdk, Gio, GLib

class FileItem:
    def __init__(self, name, path, is_dir, size=0, mtime=0):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.size = size
        self.mtime = mtime

class FileListWidget(Gtk.ScrolledWindow):
    def __init__(self, on_open_directory, on_status_change):
        super().__init__()
        self.set_hexpand(True)
        self.set_vexpand(True)

        self.on_open_directory = on_open_directory
        self.on_status_change = on_status_change
        self.current_dir = ""
        self.items = []

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
        gfile = Gio.File.new_for_path(path)

        try:
            enumerator = gfile.enumerate_children(
                "standard::name,standard::type,standard::size,time::modified",
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

        # Sort directories first, then files alphabetically (case-insensitive)
        new_items.sort(key=lambda item: (not item.is_dir, item.name.lower()))
        self.items = new_items

        # Re-populate list box
        # Remove existing rows
        while True:
            row = self.list_box.get_row_at_index(0)
            if row is None:
                break
            self.list_box.remove(row)

        for item in self.items:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row_box.set_margin_top(4)
            row_box.set_margin_bottom(4)
            row_box.set_margin_start(8)
            row_box.set_margin_end(8)

            prefix = "📁 " if item.is_dir else "   "
            label_text = f"{prefix}{item.name}{'/' if item.is_dir else ''}"
            lbl = Gtk.Label(label=label_text, xalign=0.0)
            row_box.append(lbl)

            row = Gtk.ListBoxRow()
            row.set_child(row_box)
            row.item_data = item
            self.list_box.append(row)

        # Select first row if available
        if self.items:
            first_row = self.list_box.get_row_at_index(0)
            if first_row:
                self.list_box.select_row(first_row)

        if self.on_status_change:
            self.on_status_change(f"{len(self.items)} items")

        return True

    def get_selected_item(self):
        row = self.list_box.get_selected_row()
        if row and hasattr(row, 'item_data'):
            return row.item_data
        return None

    def move_selection(self, delta):
        row = self.list_box.get_selected_row()
        idx = row.get_index() if row else 0
        new_idx = max(0, min(len(self.items) - 1, idx + delta))
        target_row = self.list_box.get_row_at_index(new_idx)
        if target_row:
            self.list_box.select_row(target_row)
            target_row.grab_focus()

    def activate_selected(self):
        item = self.get_selected_item()
        if not item:
            return

        if item.is_dir:
            self.on_open_directory(item.path)
        else:
            # Launch file via GIO default app
            gfile = Gio.File.new_for_path(item.path)
            uri = gfile.get_uri()
            Gio.AppInfo.launch_default_for_uri_async(uri, None, None, None)

    def _on_row_activated(self, list_box, row):
        if hasattr(row, 'item_data'):
            item = row.item_data
            if item.is_dir:
                self.on_open_directory(item.path)
            else:
                gfile = Gio.File.new_for_path(item.path)
                Gio.AppInfo.launch_default_for_uri_async(gfile.get_uri(), None, None, None)

    def _on_row_selected(self, list_box, row):
        if row and hasattr(row, 'item_data'):
            item = row.item_data
            if self.on_status_change:
                size_str = f" ({item.size} bytes)" if not item.is_dir else ""
                self.on_status_change(f"{item.name}{size_str}")
