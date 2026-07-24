"""
Minimal TUI Delete Confirmation Dialog for weg.
Default focus is set to 'Cancel' to prevent accidental deletion.
Supports 'y' / 'n', arrow keys (left/right/h/l), Enter, and Esc.
"""

import os
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

class DeleteConfirmWindow(Gtk.Window):
    def __init__(self, parent_win, targets, on_confirm):
        super().__init__(title="Delete Confirmation")
        self.set_transient_for(parent_win)
        self.set_modal(True)
        self.set_default_size(440, 190)
        self.targets = targets
        self.on_confirm = on_confirm

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(14)
        main_box.set_margin_bottom(14)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)

        # Title Label
        count_str = f"{len(targets)} item(s)" if len(targets) > 1 else f"'{os.path.basename(targets[0])}'"
        title_lbl = Gtk.Label(label=f"Permanently delete {count_str}?", xalign=0.0)
        title_lbl.add_css_class("path-label")
        main_box.append(title_lbl)

        # File preview list
        preview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        for p in targets[:4]:
            is_dir = os.path.isdir(p)
            name = os.path.basename(p) or p
            lbl = Gtk.Label(label=f"  {'📁' if is_dir else '📄'} {name}{'/' if is_dir else ''}", xalign=0.0)
            lbl.add_css_class("file-item")
            preview_box.append(lbl)

        if len(targets) > 4:
            more_lbl = Gtk.Label(label=f"  ... and {len(targets) - 4} more", xalign=0.0)
            more_lbl.add_css_class("hidden-item")
            preview_box.append(more_lbl)

        main_box.append(preview_box)
        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Button Bar (Default focus on Cancel to prevent accidental deletion)
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.END)

        self.cancel_btn = Gtk.Button(label="Cancel [N]")
        self.cancel_btn.set_can_focus(True)
        self.cancel_btn.connect("clicked", lambda b: self.close())
        btn_box.append(self.cancel_btn)

        self.delete_btn = Gtk.Button(label="Delete [Y]")
        self.delete_btn.set_can_focus(True)
        self.delete_btn.add_css_class("destructive-btn")
        self.delete_btn.connect("clicked", self._do_delete)
        btn_box.append(self.delete_btn)

        main_box.append(btn_box)
        self.set_child(main_box)

        # Default focus to Cancel button
        self.cancel_btn.grab_focus()

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

    def _do_delete(self, btn=None):
        self.close()
        if self.on_confirm:
            self.on_confirm(self.targets)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval in (Gdk.KEY_Escape, Gdk.KEY_n, Gdk.KEY_N, Gdk.KEY_q):
            self.close()
            return True
        elif keyval in (Gdk.KEY_y, Gdk.KEY_Y):
            self._do_delete()
            return True
        elif keyval in (Gdk.KEY_Left, Gdk.KEY_h):
            self.cancel_btn.grab_focus()
            return True
        elif keyval in (Gdk.KEY_Right, Gdk.KEY_l):
            self.delete_btn.grab_focus()
            return True
        elif keyval in (Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab):
            if self.get_focus() == self.cancel_btn:
                self.delete_btn.grab_focus()
            else:
                self.cancel_btn.grab_focus()
            return True
        elif keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            focused = self.get_focus()
            if focused == self.delete_btn:
                self._do_delete()
            else:
                self.close()
            return True
        return False

def show_delete_confirmation(parent_win, targets, on_confirm):
    win = DeleteConfirmWindow(parent_win, targets, on_confirm)
    win.present()
