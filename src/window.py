"""
Main application window for weg with Neovim / LazyVim ergonomics,
nnn-style 8-context/tab switching (keys 1-8), Omarchy global system theme support,
full multi-level Undo/Redo stack (Phase 8.1), and directory history back/forward (Phase 8.2).
"""

import os
import shutil
import subprocess
import threading
import time
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gdk, Gio, GLib

from src.path_bar import PathBarWidget
from src.file_list import FileListWidget
from src.preview_pane import PreviewPaneWidget
from src.command_bar import CommandBarWidget
from src.monitor import DirectoryMonitor
from src.help_dialog import show_help_overlay
from src.theme_dialog import show_theme_picker
from src.delete_dialog import show_delete_confirmation
from src.theme import init_theme, set_theme, get_current_theme, get_available_themes
from src.context_manager import ContextManager
from src.archive_utils import create_zip_archive, create_tar_archive, extract_archive
from src.undo_manager import UndoManager, BatchRenameRecord, MoveRecord, CopyRecord, TrashRecord
from src.frecency import FrecencyTracker

class WegWindow(Gtk.ApplicationWindow):
    def __init__(self, app, initial_dir=None):
        super().__init__(application=app, title="")
        self.set_default_size(850, 550)

        # Apply & init saved theme from ~/.config/weg/config.json
        init_theme()

        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser("~")
        self.current_dir = os.path.abspath(initial_dir)

        # Multi-Context Manager (nnn-style 1-8 tabs + Directory History)
        self.context_mgr = ContextManager(initial_dir=self.current_dir, total_contexts=8)

        # Multi-Level Undo Manager (Phase 8.1)
        self.undo_mgr = UndoManager(max_depth=50)

        # Frecency Quick Jump Engine (Phase 8.3)
        self.frecency = FrecencyTracker()

        self.display = Gdk.Display.get_default()
        self.clipboard = self.display.get_clipboard() if self.display else None

        self.monitor = DirectoryMonitor(self._on_directory_changed)
        self._last_g_time = 0

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # 1. Path Bar (Neovim bufferline style + Top-Right 1-8 Context Indicator)
        self.path_bar = PathBarWidget(
            on_navigate=self.navigate_to,
            on_context_click=self.switch_context
        )
        main_box.append(self.path_bar)
        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # 2. Content Area (File List + Preview Pane)
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        content_box.set_vexpand(True)

        self.file_list = FileListWidget(
            on_open_directory=self.navigate_to,
            on_status_change=self._on_file_list_status_change
        )
        content_box.append(self.file_list)

        self.preview_pane = PreviewPaneWidget()
        self.preview_pane.add_css_class("preview-pane")
        self.preview_pane.set_visible(False)
        content_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        content_box.append(self.preview_pane)

        main_box.append(content_box)
        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # 3. Status Bar
        self.status_bar = Gtk.Label(label="Press ? for keybinding help", xalign=0.0)
        self.status_bar.set_use_underline(False)
        self.status_bar.add_css_class("status-bar")
        main_box.append(self.status_bar)

        # 4. Command Bar (Neovim lualine style)
        self.command_bar = CommandBarWidget(
            on_filter_change=self.file_list.filter_local,
            on_search_query=self.file_list.search_recursive,
            on_command_execute=self.execute_command,
            on_cancel=self._on_command_cancel,
            on_filter_activate=self.file_list.try_auto_open_single_folder
        )
        main_box.append(self.command_bar)

        self.set_child(main_box)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

        self.navigate_to(self.current_dir)

    def navigate_to(self, path, record_history=True):
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            return

        if record_history and path != self.current_dir:
            active_ctx = self.context_mgr.get_active()
            active_ctx.push_history(path)

        self.current_dir = path
        if hasattr(self, 'frecency'):
            self.frecency.record_visit(path)

        self.path_bar.set_path(path)
        self.file_list.load_directory(path)
        self.monitor.set_directory(path)
        self.file_list.grab_focus()

    def go_back(self):
        active_ctx = self.context_mgr.get_active()
        prev_path = active_ctx.go_back()
        if prev_path:
            self.navigate_to(prev_path, record_history=False)
            self.update_status(f"History Back: {os.path.basename(prev_path) or prev_path}")
        else:
            self.update_status("Already at oldest history entry")

    def go_forward(self):
        active_ctx = self.context_mgr.get_active()
        next_path = active_ctx.go_forward()
        if next_path:
            self.navigate_to(next_path, record_history=False)
            self.update_status(f"History Forward: {os.path.basename(next_path) or next_path}")
        else:
            self.update_status("Already at newest history entry")

    def undo(self):
        ok, msg = self.undo_mgr.undo()
        self.update_status(msg)
        if ok:
            self.file_list.load_directory(self.current_dir)

    def redo(self):
        ok, msg = self.undo_mgr.redo()
        self.update_status(msg)
        if ok:
            self.file_list.load_directory(self.current_dir)

    def switch_context(self, target_context_id):
        if not (1 <= target_context_id <= 8):
            return

        # Save active context state
        curr = self.context_mgr.get_active()
        curr.current_dir = self.current_dir
        curr.selected_paths = set(self.file_list.selected_paths)
        curr.show_hidden = self.file_list.show_hidden

        # Switch to target context
        nxt = self.context_mgr.set_active_context(target_context_id)
        if not nxt:
            return

        self.path_bar.update_contexts(active_id=target_context_id)
        self.file_list.show_hidden = nxt.show_hidden
        self.file_list.selected_paths = set(nxt.selected_paths)
        self.navigate_to(nxt.current_dir, record_history=False)
        self.update_status(f"Switched to Context {target_context_id} ({os.path.basename(nxt.current_dir) or nxt.current_dir})")

    def update_status(self, text):
        self.status_bar.set_text(text)

    def _on_file_list_status_change(self, text):
        self.update_status(text)
        if self.preview_pane.get_visible():
            item = self.file_list.get_focused_item()
            if item:
                self.preview_pane.preview_file(item.path)
            else:
                self.preview_pane.clear()

    def toggle_preview(self):
        is_visible = not self.preview_pane.get_visible()
        self.preview_pane.set_visible(is_visible)
        if is_visible:
            item = self.file_list.get_focused_item()
            if item:
                self.preview_pane.preview_file(item.path)

    def show_help(self):
        show_help_overlay(self)

    def show_themes(self):
        show_theme_picker(self)

    def _on_directory_changed(self):
        if self.current_dir and not self.command_bar.mode:
            self.file_list.load_directory(self.current_dir)

    def _on_command_cancel(self, keep_filter=False):
        if not keep_filter:
            self.file_list.load_directory(self.current_dir)
        self.file_list.grab_focus()

    def move_selection_to_trash(self):
        targets = self.file_list.get_target_files()
        if not targets:
            return

        trashed_paths = []
        for path in targets:
            try:
                gfile = Gio.File.new_for_path(path)
                gfile.trash(None)
                trashed_paths.append(path)
            except Exception as e:
                print(f"[Window] Trash error for {path}: {e}")

        if trashed_paths:
            self.undo_mgr.push(TrashRecord(trashed_paths))

        self.file_list.load_directory(self.current_dir)
        self.update_status(f"Moved {len(trashed_paths)} item(s) to Trash (u to undo)")

    def permanent_delete_selection(self, confirm_bypass=False):
        targets = self.file_list.get_target_files()
        if not targets:
            return

        if not confirm_bypass:
            show_delete_confirmation(self, targets, self._do_permanent_delete)
        else:
            self._do_permanent_delete(targets)

    def _do_permanent_delete(self, targets):
        deleted_count = 0
        for t in targets:
            try:
                if os.path.isdir(t):
                    shutil.rmtree(t, ignore_errors=True)
                elif os.path.exists(t):
                    os.remove(t)
                deleted_count += 1
            except Exception as e:
                print(f"[Window] Delete error for {t}: {e}")

        self.file_list.load_directory(self.current_dir)
        self.update_status(f"Permanently deleted {deleted_count} item(s)")

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
                src_paths = []
                dest_paths = []

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
                        src_paths.append(src_path)
                        dest_paths.append(dest_path)

                if dest_paths:
                    if action == "cut":
                        for sp, dp in zip(src_paths, dest_paths):
                            self.undo_mgr.push(MoveRecord(sp, dp))
                    else:
                        self.undo_mgr.push(CopyRecord(dest_paths, src_paths))

                self.file_list.load_directory(self.current_dir)
                self.update_status(f"Pasted {len(dest_paths)} item(s) (u to undo)")
        except Exception as e:
            print(f"[Window] Paste error: {e}")

    def _on_clipboard_file_list_done(self, clipboard, result, user_data):
        try:
            val = clipboard.read_value_finish(result)
            if isinstance(val, Gdk.FileList):
                src_paths = []
                dest_paths = []
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
                        src_paths.append(src_path)
                        dest_paths.append(dest_path)

                if dest_paths:
                    self.undo_mgr.push(CopyRecord(dest_paths, src_paths))

                self.file_list.load_directory(self.current_dir)
                self.update_status(f"Pasted {len(dest_paths)} item(s) (u to undo)")
        except Exception as e:
            print(f"[Window] Paste GdkFileList error: {e}")

    def _run_async_shell_command(self, cmd_text):
        self.update_status(f"Executing: {cmd_text}...")

        def _worker():
            try:
                res = subprocess.run(cmd_text, shell=True, cwd=self.current_dir, capture_output=True, text=True, timeout=30)
                msg = res.stdout.strip() or res.stderr.strip() or f"Command exit code: {res.returncode}"
            except subprocess.TimeoutExpired:
                msg = "Command timed out (30s)"
            except Exception as e:
                msg = f"Execution error: {e}"

            def _on_done():
                self.update_status(msg[:100])
                self.file_list.load_directory(self.current_dir)
                return False

            GLib.idle_add(_on_done)

        threading.Thread(target=_worker, daemon=True).start()

    def execute_command(self, cmd_text):
        parts = cmd_text.split(maxsplit=1)
        if not parts:
            return

        verb = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if verb in ("help", "hint", "?"):
            self.show_help()
            return

        if verb in ("z", "jump"):
            if not arg:
                self.update_status("Usage: :z <fragment> (frecency quick jump)")
                return
            target = self.frecency.query(arg)
            if target:
                self.navigate_to(target)
                self.update_status(f"Jumped to '{target}'")
            else:
                self.update_status(f"No matching frecent directory for '{arg}'")
            return

        if verb in ("undo",):
            self.undo()
            return

        if verb in ("redo",):
            self.redo()
            return

        if verb in ("back",):
            self.go_back()
            return

        if verb in ("forward",):
            self.go_forward()
            return

        if verb in ("theme", "themes"):
            if not arg or arg in ("select", "menu"):
                self.show_themes()
            else:
                ok, msg = set_theme(arg)
                self.update_status(msg)
            return

        if verb in ("icon", "icons", "iconset"):
            if not arg:
                self.update_status(f"Current iconset: '{self.file_list.iconset}'. Available: nerdfont, minimal, unicode")
            else:
                ok, msg = self.file_list.set_iconset(arg)
                self.update_status(msg)
            return

        if verb in ("context", "tab"):
            if arg.isdigit() and 1 <= int(arg) <= 8:
                self.switch_context(int(arg))
            else:
                self.update_status(f"Current context: {self.context_mgr.active_id}. Usage: :context <1-8>")
            return

        if verb in ("zip", "tar"):
            targets = self.file_list.get_target_files()
            if not targets:
                self.update_status("No files selected to archive")
                return

            default_name = os.path.basename(targets[0]) if len(targets) == 1 else "archive"
            archive_name = arg if arg else default_name
            out_path = os.path.join(self.current_dir, archive_name)

            self.update_status(f"Compressing {len(targets)} item(s)...")

            def _zip_worker():
                try:
                    if verb == "zip":
                        res_path = create_zip_archive(targets, out_path)
                    else:
                        res_path = create_tar_archive(targets, out_path)
                    msg = f"Created '{os.path.basename(res_path)}'"
                except Exception as e:
                    msg = f"Archive error: {e}"

                def _on_zip_done():
                    self.update_status(msg)
                    self.file_list.load_directory(self.current_dir)
                    return False

                GLib.idle_add(_on_zip_done)

            threading.Thread(target=_zip_worker, daemon=True).start()
            return

        if verb in ("unzip", "extract", "untar"):
            targets = self.file_list.get_target_files()
            archive_path = targets[0] if (targets and os.path.exists(targets[0])) else (os.path.join(self.current_dir, arg) if arg else None)
            if not archive_path or not os.path.exists(archive_path):
                self.update_status("Select an archive file to extract")
                return

            self.update_status(f"Extracting '{os.path.basename(archive_path)}'...")

            def _extract_worker():
                try:
                    ok, msg = extract_archive(archive_path, self.current_dir)
                except Exception as e:
                    msg = f"Extract error: {e}"

                def _on_extract_done():
                    self.update_status(msg)
                    self.file_list.load_directory(self.current_dir)
                    return False

                GLib.idle_add(_on_extract_done)

            threading.Thread(target=_extract_worker, daemon=True).start()
            return

        if verb in ("q", "quit"):
            app = self.get_application()
            if app:
                app.quit()
            return

        if verb in ("mkdir", "newfolder"):
            if arg:
                target = os.path.join(self.current_dir, arg)
                os.makedirs(target, exist_ok=True)
                self.update_status(f"Created folder '{arg}'")
        elif verb in ("touch", "newfile"):
            if arg:
                target = os.path.join(self.current_dir, arg)
                open(target, "a").close()
                self.update_status(f"Created file '{arg}'")
        elif verb in ("new",):
            if arg.startswith("folder "):
                folder_name = arg[7:].strip()
                if folder_name:
                    target = os.path.join(self.current_dir, folder_name)
                    os.makedirs(target, exist_ok=True)
                    self.update_status(f"Created folder '{folder_name}'")
            elif arg.startswith("file "):
                file_name = arg[5:].strip()
                if file_name:
                    target = os.path.join(self.current_dir, file_name)
                    open(target, "a").close()
                    self.update_status(f"Created file '{file_name}'")
            else:
                target = os.path.join(self.current_dir, arg)
                if "." in arg:
                    open(target, "a").close()
                    self.update_status(f"Created file '{arg}'")
                else:
                    os.makedirs(target, exist_ok=True)
                    self.update_status(f"Created folder '{arg}'")

        elif verb in ("rename", "mv"):
            targets = self.file_list.get_target_files()
            if not targets or not arg:
                return

            rename_pairs = []
            if len(targets) == 1:
                old_path = targets[0]
                new_path = os.path.join(os.path.dirname(old_path), arg)
                os.rename(old_path, new_path)
                rename_pairs.append((old_path, new_path))
                self.update_status(f"Renamed to '{arg}' (u to undo)")
            else:
                for idx, old_path in enumerate(targets, 1):
                    ext = os.path.splitext(old_path)[1]
                    if "{n}" in arg:
                        new_name = arg.replace("{n}", str(idx))
                    else:
                        new_name = f"{arg}_{idx}{ext}"
                    new_path = os.path.join(os.path.dirname(old_path), new_name)
                    os.rename(old_path, new_path)
                    rename_pairs.append((old_path, new_path))
                self.update_status(f"Batch renamed {len(targets)} item(s) (u to undo)")

            if rename_pairs:
                self.undo_mgr.push(BatchRenameRecord(rename_pairs))

        elif verb in ("delete", "rm"):
            self.permanent_delete_selection()

        else:
            self._run_async_shell_command(cmd_text)

        self.file_list.load_directory(self.current_dir)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        focus = self.get_focus()
        if focus in (self.path_bar.path_entry, self.command_bar.entry):
            return False

        ctrl_pressed = bool(state & Gdk.ModifierType.CONTROL_MASK)
        alt_pressed = bool(state & Gdk.ModifierType.ALT_MASK)

        # Directory History Back / Forward (Alt+Left / Alt+Right or Alt+h / Alt+l or Ctrl+O / Ctrl+I)
        if (alt_pressed and keyval in (Gdk.KEY_Left, Gdk.KEY_h)) or (ctrl_pressed and keyval == Gdk.KEY_o):
            self.go_back()
            return True

        if (alt_pressed and keyval in (Gdk.KEY_Right, Gdk.KEY_l)) or (ctrl_pressed and keyval == Gdk.KEY_i):
            self.go_forward()
            return True

        # Multi-Level Undo / Redo (u or Ctrl+Z to Undo, Ctrl+R or Ctrl+Y to Redo)
        if (keyval == Gdk.KEY_u and not ctrl_pressed and not alt_pressed) or (ctrl_pressed and keyval == Gdk.KEY_z):
            self.undo()
            return True

        if (ctrl_pressed and keyval in (Gdk.KEY_r, Gdk.KEY_y)):
            self.redo()
            return True

        # nnn-style Context / Tab switching using keys 1-8
        if keyval in (Gdk.KEY_1, Gdk.KEY_2, Gdk.KEY_3, Gdk.KEY_4, Gdk.KEY_5, Gdk.KEY_6, Gdk.KEY_7, Gdk.KEY_8) and not ctrl_pressed and not alt_pressed:
            target_c_id = keyval - Gdk.KEY_0
            self.switch_context(target_c_id)
            return True

        if ctrl_pressed and keyval == Gdk.KEY_d:
            self.file_list.jump_half_page(1)
            return True

        if ctrl_pressed and keyval == Gdk.KEY_u:
            self.file_list.jump_half_page(-1)
            return True

        if keyval == Gdk.KEY_g and not ctrl_pressed and not (state & Gdk.ModifierType.SHIFT_MASK):
            now = time.time()
            if now - self._last_g_time < 0.5:
                self.file_list.jump_to_first()
                self._last_g_time = 0
            else:
                self._last_g_time = now
            return True

        if (state & Gdk.ModifierType.SHIFT_MASK) and keyval == Gdk.KEY_G:
            self.file_list.jump_to_last()
            return True

        if keyval in (Gdk.KEY_question, Gdk.KEY_F1):
            self.show_help()
            return True

        if keyval == Gdk.KEY_q and not ctrl_pressed:
            app = self.get_application()
            if app:
                app.quit()
            return True

        if keyval in (Gdk.KEY_asciitilde, Gdk.KEY_dead_tilde):
            self.navigate_to(os.path.expanduser("~"))
            return True

        if (keyval == Gdk.KEY_period and not ctrl_pressed) or (ctrl_pressed and keyval in (Gdk.KEY_h, Gdk.KEY_H)):
            self.file_list.toggle_hidden_files()
            return True

        if keyval == Gdk.KEY_Tab:
            self.toggle_preview()
            return True

        if ctrl_pressed and (keyval in (Gdk.KEY_c, Gdk.KEY_C)):
            self.copy_selection_to_clipboard(action="copy")
            return True

        if ctrl_pressed and (keyval in (Gdk.KEY_x, Gdk.KEY_X)):
            self.copy_selection_to_clipboard(action="cut")
            return True

        if ctrl_pressed and (keyval in (Gdk.KEY_v, Gdk.KEY_V)):
            self.paste_from_clipboard()
            return True

        if (state & Gdk.ModifierType.SHIFT_MASK) and keyval == Gdk.KEY_X:
            self.permanent_delete_selection()
            return True

        if keyval == Gdk.KEY_x and not ctrl_pressed:
            self.move_selection_to_trash()
            return True

        if ctrl_pressed and (keyval in (Gdk.KEY_l, Gdk.KEY_L)):
            self.path_bar.start_editing()
            return True

        if keyval == Gdk.KEY_slash:
            self.command_bar.activate_mode('/')
            return True
        elif keyval == Gdk.KEY_greater:
            self.command_bar.activate_mode('>')
            return True
        elif keyval == Gdk.KEY_colon:
            self.command_bar.activate_mode(':')
            return True

        elif keyval == Gdk.KEY_z and not ctrl_pressed and not alt_pressed:
            self.command_bar.activate_mode(':', initial_text="z ")
            return True

        elif keyval == Gdk.KEY_space:
            self.file_list.toggle_selection_focused()
            return True

        elif keyval == Gdk.KEY_r and not ctrl_pressed and not alt_pressed:
            self.command_bar.activate_mode(':', initial_text="rename ")
            return True

        elif keyval in (Gdk.KEY_Up, Gdk.KEY_k):
            self.file_list.move_selection(-1)
            return True

        elif keyval in (Gdk.KEY_Down, Gdk.KEY_j):
            self.file_list.move_selection(1)
            return True

        elif keyval in (Gdk.KEY_Right, Gdk.KEY_l, Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.file_list.activate_selected()
            return True

        elif keyval in (Gdk.KEY_Left, Gdk.KEY_h, Gdk.KEY_BackSpace):
            parent = os.path.dirname(self.current_dir)
            if parent and parent != self.current_dir:
                self.navigate_to(parent)
            return True

        return False
