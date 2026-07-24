#!/usr/bin/env /usr/bin/python3
"""
Spike 1a: GTK4 Native Drag & Drop with Nautilus on Hyprland/Wayland.
Tests drag-in (DropTarget) and drag-out (DragSource) with Gdk.FileList / GFile.
"""

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gdk, Gio, GLib

class DndSpikeWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Spike 1a: GTK4 DnD Test")
        self.set_default_size(500, 350)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)

        # Log view
        self.log_buffer = Gtk.TextBuffer()
        self.log_view = Gtk.TextView(buffer=self.log_buffer)
        self.log_view.set_editable(False)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.log_view)
        scrolled.set_vexpand(True)

        # Drop Zone (Drag IN from Nautilus)
        self.drop_label = Gtk.Label(label="DROP ZONE: Drag file(s) from Nautilus here")
        self.drop_frame = Gtk.Frame()
        self.drop_frame.set_child(self.drop_label)
        self.drop_frame.set_size_request(-1, 80)
        
        # Configure Gtk.DropTarget explicitly with COPY | MOVE
        drop_target = Gtk.DropTarget.new(
            type=Gdk.FileList,
            actions=Gdk.DragAction.COPY | Gdk.DragAction.MOVE
        )
        drop_target.connect("enter", self.on_drop_enter)
        drop_target.connect("drop", self.on_drop)
        self.drop_frame.add_controller(drop_target)

        # Drag Source (Drag OUT to Nautilus)
        self.drag_button = Gtk.Button(label="DRAG ME: Drag this file button into Nautilus")
        self.drag_file_path = "/tmp/weg_dnd_test.txt"
        with open(self.drag_file_path, "w") as f:
            f.write("Hello from weg DnD spike!\n")
        
        drag_source = Gtk.DragSource.new()
        drag_source.set_actions(Gdk.DragAction.COPY | Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self.on_drag_prepare)
        drag_source.connect("drag-begin", self.on_drag_begin)
        drag_source.connect("drag-end", self.on_drag_end)
        self.drag_button.add_controller(drag_source)

        main_box.append(self.drop_frame)
        main_box.append(self.drag_button)
        main_box.append(scrolled)
        self.set_child(main_box)

        self.log("Ready. Test dragging files into Drop Zone, or dragging button out to Nautilus.")

    def log(self, text):
        print(f"[DnD Spike] {text}")
        end_iter = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end_iter, text + "\n")

    def on_drop_enter(self, target, x, y):
        self.log(f"-> DROP ENTER fired at ({x}, {y})! Actions offered by target: COPY | MOVE")
        return Gdk.DragAction.COPY | Gdk.DragAction.MOVE

    def on_drop(self, target, value, x, y):
        self.log(f"-> DROP FIRED! Value type: {type(value)}")
        if isinstance(value, Gdk.FileList):
            files = value.get_files()
            for f in files:
                self.log(f"   Received file: {f.get_path()}")
            return True
        elif hasattr(value, "get_files"):
            for f in value.get_files():
                self.log(f"   Received file: {f.get_path()}")
            return True
        else:
            self.log(f"   Received unknown value: {value}")
            return False

    def on_drag_prepare(self, source, x, y):
        self.log(f"<- DRAG PREPARE for file: {self.drag_file_path}")
        gfile = Gio.File.new_for_path(self.drag_file_path)
        file_list = Gdk.FileList.new_from_list([gfile])
        provider = Gdk.ContentProvider.new_for_value(file_list)
        return provider

    def on_drag_begin(self, source, drag):
        self.log("<- DRAG BEGIN")

    def on_drag_end(self, source, drag, delete_data):
        self.log(f"<- DRAG END (delete_data={delete_data})")

def main():
    app = Gtk.Application(application_id="fm.weg.Spike1a")
    def on_activate(a):
        win = DndSpikeWindow(a)
        win.present()
        if "--auto-test" in sys.argv:
            GLib.timeout_add(1000, a.quit)
    app.connect("activate", on_activate)
    return app.run([sys.argv[0]])

if __name__ == "__main__":
    sys.exit(main())
