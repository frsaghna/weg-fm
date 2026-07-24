"""
Main application window for weg.
Connects CommandBar (/ > :), keyboard shortcuts (Ctrl+C, Ctrl+X, Ctrl+V, Ctrl+L),
and handles file operations & clipboard integration.
"""

import os
import shutil
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gdk, Gio, GLib

from src.path_bar import PathBarWidget
from src.file_list import FileListWidget
from src.command_bar import CommandBarWidget
from src.monitor import DirectoryMonitor

class WegWindow(Gtk.ApplicationWindow):
    def __init__(self, app, initial_dir=None):
        super().__init__(application=app, title="weg")
        self.set_default_size(700, 500)

        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser("~")
        self.current_dir = os.path.abspath(initial_dir)

        self.display = Gdk.Display.get_default()
        self.clipboard = self.display.get_clipboard() if self.display else None

        self.monitor = DirectoryMonitor(self._on_directory_changed)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # 1. Path Bar
        self.path_bar = PathBarWidget(on_navigate=self.navigate_to)
        main_box.append(self.path_bar)
        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # 2. File List
        self.file_list = FileListWidget(
            on_open_directory=self.navigate_to,
            on_status_change=self.update_status
        )
        main_box.append(self.file_list)
        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # 3. Status Bar
        self.status_bar = Gtk.Label(label="Ready", xalign=0.0)
        self.status_bar.set_margin_top(4)
        self.status_bar.set_margin_bottom(4)
        self.status_bar.set_margin_start(12)
        self.status_bar.set_margin_end(12)
        main_box.append(self.status_bar)

        # 4. Command Bar (persistent at bottom)
        self.command_bar = CommandBarWidget(
            on_filter_change=self.file_list.filter_local,
            on_search_query=self.file_list.search_recursive,
            on_command_execute=self.execute_command,
            on_cancel=self._on_command_cancel
        )
        main_box.append(self.command_bar)

        self.set_child(main_box)

        # Keyboard Navigation Controller
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

        self.navigate_to(self.current_dir)

    def navigate_to(self, path):
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            return

        self.current_dir = path
        self.path_bar.set_path(path)
        self.file_list.load_directory(path)
        self.monitor.set_directory(path)
        self.file_list.grab_focus()

    def update_status(self, text):
        self.status_bar.set_text(text)

    def _on_directory_changed(self):
        if self.current_dir and not self.command_bar.mode:
            self.file_list.load_directory(self.current_dir)

    def _on_command_cancel(self, keep_filter=False):
        if not keep_filter:
            self.file_list.load_directory(self.current_dir)
        self.file_list.grab_focus()

    def copy_selection_to_clipboard(self, action="copy"):
        targets = self.file_list.get_target_files()
        if not targets or not self.clipboard:
            return

        uris = [Gio.File.new_for_path(p).get_uri() for p in targets]
        payload_str = f"{action}\n" + "\n".join(uris) + "\0"
        payload_bytes = payload_str.encode('utf-8')
        gbytes = GLib.Bytes.new(payload_bytes)

        gnome_provider = Gdk.ContentProvider.new_for_bytes("x-special/gnome-copied-files", gbytes)
        gfiles = [Gio.File.new_for_path(p) for p in targets]
        file_list = Gdk.FileList.new_from_list(gfiles)
        file_list_provider = Gdk.ContentProvider.new_for_value(file_list)

        union_provider = Gdk.ContentProvider.new_union([gnome_provider, file_list_provider])
        self.clipboard.set_content(union_provider)
        self.update_status(f"Clipboard: {action.upper()} {len(targets)} item(s)")

    def paste_from_clipboard(self):
        if not self.clipboard:
            return

        formats = self.clipboard.get_formats()
        mime_types = formats.get_mime_types()

        if "x-special/gnome-copied-files" in mime_types:
            self.clipboard.read_async(["x-special/gnome-copied-files"], GLib.PRIORITY_DEFAULT, None, self._on_clipboard_read_done, None)
        elif formats.contain_gtype(Gdk.FileList):
            self.clipboard.read_value_async(Gdk.FileList, GLib.PRIORITY_DEFAULT, None, self._on_clipboard_file_list_done, None)

    def _on_clipboard_read_done(self, clipboard, result, user_data):
        try:
            stream, mime_type = clipboard.read_finish(result)
            if stream:
                gbytes = stream.read_bytes(8192, None)
                data = gbytes.get_data().decode('utf-8', errors='replace').rstrip('\x00')
                lines = [l for l in data.split('\n') if l.strip()]
                if not lines:
                    return

                action = lines[0].lower()
                uris = lines[1:]
                count = 0
                for uri in uris:
                    gfile = Gio.File.new_for_uri(uri)
                    src_path = gfile.get_path()
                    if src_path and os.path.exists(src_path):
                        dest_name = os.path.basename(src_path)
                        dest_path = os.path.join(self.current_dir, dest_name)
                        if src_path == dest_path:
                            continue
                        if action == "cut":
                            shutil.move(src_path, dest_path)
                        else:
                            if os.path.isdir(src_path):
                                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                            else:
                                shutil.copy2(src_path, dest_path)
                        count += 1
                self.file_list.load_directory(self.current_dir)
                self.update_status(f"Pasted {count} item(s)")
        except Exception as e:
            print(f"[Window] Paste error: {e}")

    def _on_clipboard_file_list_done(self, clipboard, result, user_data):
        try:
            val = clipboard.read_value_finish(result)
            if isinstance(val, Gdk.FileList):
                count = 0
                for f in val.get_files():
                    src_path = f.get_path()
                    if src_path and os.path.exists(src_path):
                        dest_name = os.path.basename(src_path)
                        dest_path = os.path.join(self.current_dir, dest_name)
                        if src_path == dest_path:
                            continue
                        if os.path.isdir(src_path):
                            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                        else:
                            shutil.copy2(src_path, dest_path)
                        count += 1
                self.file_list.load_directory(self.current_dir)
                self.update_status(f"Pasted {count} item(s)")
        except Exception as e:
            print(f"[Window] Paste GdkFileList error: {e}")

    def execute_command(self, cmd_text):
        parts = cmd_text.split(maxsplit=1)
        if not parts:
            return

        verb = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if verb in ("new", "touch", "mkdir"):
            if arg.startswith("folder "):
                folder_name = arg[7:].strip()
                if folder_name:
                    target = os.path.join(self.current_dir, folder_name)
                    os.makedirs(target, exist_ok=True)
            elif arg.startswith("file "):
                file_name = arg[5:].strip()
                if file_name:
                    target = os.path.join(self.current_dir, file_name)
                    open(target, "a").close()
            else:
                target = os.path.join(self.current_dir, arg)
                if "." in arg:
                    open(target, "a").close()
                else:
                    os.makedirs(target, exist_ok=True)

        elif verb in ("rename", "mv"):
            targets = self.file_list.get_target_files()
            if not targets or not arg:
                return

            if len(targets) == 1:
                old_path = targets[0]
                new_path = os.path.join(os.path.dirname(old_path), arg)
                os.rename(old_path, new_path)
            else:
                for idx, old_path in enumerate(targets, 1):
                    ext = os.path.splitext(old_path)[1]
                    if "{n}" in arg:
                        new_name = arg.replace("{n}", str(idx))
                    else:
                        new_name = f"{arg}_{idx}{ext}"
                    new_path = os.path.join(os.path.dirname(old_path), new_name)
                    os.rename(old_path, new_path)

        elif verb in ("delete", "rm"):
            targets = self.file_list.get_target_files()
            for t in targets:
                if os.path.isdir(t):
                    shutil.rmtree(t, ignore_errors=True)
                elif os.path.exists(t):
                    os.remove(t)

        self.file_list.load_directory(self.current_dir)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        focus = self.get_focus()
        if focus in (self.path_bar.path_entry, self.command_bar.entry):
            return False

        ctrl_pressed = bool(state & Gdk.ModifierType.CONTROL_MASK)

        # Ctrl+C: Copy to clipboard
        if ctrl_pressed and (keyval in (Gdk.KEY_c, Gdk.KEY_C)):
            self.copy_selection_to_clipboard(action="copy")
            return True

        # Ctrl+X: Cut to clipboard
        if ctrl_pressed and (keyval in (Gdk.KEY_x, Gdk.KEY_X)):
            self.copy_selection_to_clipboard(action="cut")
            return True

        # Ctrl+V: Paste from clipboard
        if ctrl_pressed and (keyval in (Gdk.KEY_v, Gdk.KEY_V)):
            self.paste_from_clipboard()
            return True

        # Ctrl+L: Direct path editing
        if ctrl_pressed and (keyval in (Gdk.KEY_l, Gdk.KEY_L)):
            self.path_bar.start_editing()
            return True

        # Command mode triggers: /, >, :
        if keyval == Gdk.KEY_slash:
            self.command_bar.activate_mode('/')
            return True
        elif keyval == Gdk.KEY_greater:
            self.command_bar.activate_mode('>')
            return True
        elif keyval == Gdk.KEY_colon:
            self.command_bar.activate_mode(':')
            return True

        # Space: Toggle multi-selection on focused item
        elif keyval == Gdk.KEY_space:
            self.file_list.toggle_selection_focused()
            return True

        # r: Quick inline rename
        elif keyval == Gdk.KEY_r:
            self.command_bar.activate_mode(':')
            self.command_bar.entry.set_text("rename ")
            self.command_bar.entry.set_position(-1)
            return True

        # Navigation: ↑/k, ↓/j
        elif keyval in (Gdk.KEY_Up, Gdk.KEY_k):
            self.file_list.move_selection(-1)
            return True
        elif keyval in (Gdk.KEY_Down, Gdk.KEY_j):
            self.file_list.move_selection(1)
            return True

        # Enter: Activate selected
        elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.file_list.activate_selected()
            return True

        # Backspace: Parent directory
        elif keyval == Gdk.KEY_BackSpace:
            parent = os.path.dirname(self.current_dir)
            if parent and parent != self.current_dir:
                self.navigate_to(parent)
            return True

        return False
