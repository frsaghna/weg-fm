"""
Custom TUI Delete Confirmation Dialog for weg.
Coherent with the rest of the TUI aesthetic (Which-Key / Telescope floating dialog).
"""

import os
import gi

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk

class DeleteConfirmWindow(Gtk.Window):
    def __init__(self, parent_win, targets, on_confirm):
        super().__init__(title="Confirm Delete")
        self.set_transient_for(parent_win)
        self.set_modal(True)
        self.set_default_size(520, 320)
        self.targets = targets
        self.on_confirm = on_confirm

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)

        # Header Banner
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        badge = Gtk.Label(label="[ DANGER ]")
        badge.add_css_class("mode-badge-cmd")
        title = Gtk.Label(label="PERMANENT DELETE CONFIRMATION", xalign=0.0)
        title.add_css_class("path-label")

        header_box.append(badge)
        header_box.append(title)
        main_box.append(header_box)
        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Content Card
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.add_css_class("help-card")

        warning_lbl = Gtk.Label(
            label=f"Are you sure you want to permanently delete {len(targets)} item(s)?\nThis action CANNOT be undone.",
            xalign=0.0
        )
        warning_lbl.add_css_class("key-desc")
        card.append(warning_lbl)
        card.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Target Files List
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        file_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        file_list_box.set_margin_top(4)

        for path in targets[:15]: # Show up to 15 items
            is_dir = os.path.isdir(path)
            icon = "📁" if is_dir else "📄"
            name = os.path.basename(path) or path
            lbl = Gtk.Label(label=f"  {icon}  {name}{'/' if is_dir else ''}", xalign=0.0)
            lbl.add_css_class("dir-item" if is_dir else "file-item")
            file_list_box.append(lbl)

        if len(targets) > 15:
            more_lbl = Gtk.Label(label=f"  ... and {len(targets) - 15} more item(s)", xalign=0.0)
            more_lbl.add_css_class("hidden-item")
            file_list_box.append(more_lbl)

        scrolled.set_child(file_list_box)
        card.append(scrolled)
        main_box.append(card)

        # Action Footer
        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lbl_y = Gtk.Label(label=" y / Enter ")
        lbl_y.add_css_class("key-cap")
        desc_y = Gtk.Label(label="Delete")
        desc_y.add_css_class("key-desc")

        lbl_n = Gtk.Label(label=" n / Esc ")
        lbl_n.add_css_class("key-cap")
        desc_n = Gtk.Label(label="Cancel")
        desc_n.add_css_class("key-desc")

        info_box.append(lbl_y)
        info_box.append(desc_y)
        info_box.append(Gtk.Label(label="   "))
        info_box.append(lbl_n)
        info_box.append(desc_n)
        info_box.set_hexpand(True)

        cancel_btn = Gtk.Button(label="Cancel (n)")
        cancel_btn.connect("clicked", lambda b: self.close())

        delete_btn = Gtk.Button(label="Permanently Delete (y)")
        delete_btn.add_css_class("mode-badge-cmd")
        delete_btn.connect("clicked", self._on_delete_clicked)

        footer_box.append(info_box)
        footer_box.append(cancel_btn)
        footer_box.append(delete_btn)
        main_box.append(footer_box)

        self.set_child(main_box)

        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

    def _on_delete_clicked(self, btn):
        self.close()
        if self.on_confirm:
            self.on_confirm(self.targets)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval in (Gdk.KEY_Escape, Gdk.KEY_n, Gdk.KEY_q):
            self.close()
            return True
        elif keyval in (Gdk.KEY_y, Gdk.KEY_Y, Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self.close()
            if self.on_confirm:
                self.on_confirm(self.targets)
            return True
        return False

def show_delete_confirmation(parent_win, targets, on_confirm):
    win = DeleteConfirmWindow(parent_win, targets, on_confirm)
    win.present()
