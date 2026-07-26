"""
Preview pane widget for weg.
Renders text previews for text files and thumbnail image previews for images/media.
"""

import os
import hashlib
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio

class PreviewPaneWidget(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_size_request(260, -1)

        self.title_label = Gtk.Label(label="Preview", xalign=0.0)
        self.title_label.set_markup("<b>Preview</b>")
        self.append(self.title_label)

        # Image / Thumbnail view
        self.picture = Gtk.Picture()
        self.picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.picture.set_size_request(240, 240)
        self.append(self.picture)

        # Text View for text/code preview
        self.text_buffer = Gtk.TextBuffer()
        self.text_view = Gtk.TextView(buffer=self.text_buffer)
        self.text_view.set_editable(False)
        self.text_view.set_monospace(True)
        
        self.scrolled_text = Gtk.ScrolledWindow()
        self.scrolled_text.set_child(self.text_view)
        self.scrolled_text.set_vexpand(True)
        self.append(self.scrolled_text)

        self.current_path = None

    def preview_file(self, path):
        if not path or not os.path.exists(path) or os.path.isdir(path):
            self.clear()
            return

        self.current_path = path
        gfile = Gio.File.new_for_path(path)
        uri = gfile.get_uri()

        # Check if file is image or media
        pixbuf = self._load_thumbnail_or_pixbuf(path, uri)
        if pixbuf:
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.picture.set_paintable(texture)
            self.picture.set_visible(True)
            self.scrolled_text.set_visible(False)
        else:
            self.picture.set_visible(False)
            self.scrolled_text.set_visible(True)
            self._load_text_preview(path)

    def clear(self):
        self.current_path = None
        self.picture.set_paintable(None)
        self.picture.set_visible(False)
        self.text_buffer.set_text("")
        self.scrolled_text.set_visible(False)

    def _load_thumbnail_or_pixbuf(self, path, uri):
        # 1. Direct Pixbuf decode for images
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 256, 256, True)
            if pixbuf:
                return pixbuf
        except Exception:
            pass

        # 2. Check Freedesktop Thumbnail Spec cache (~/.cache/thumbnails/)
        md5_uri = hashlib.md5(uri.encode('utf-8')).hexdigest()
        cache_home = os.path.expanduser("~/.cache/thumbnails")
        for size_dir in ("large", "normal"):
            thumb_path = os.path.join(cache_home, size_dir, f"{md5_uri}.png")
            if os.path.exists(thumb_path):
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(thumb_path, 256, 256, True)
                    if pixbuf:
                        return pixbuf
                except Exception:
                    pass

        return None

    def _load_text_preview(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = [f.readline() for _ in range(100)]
                content = "".join(lines)
                self.text_buffer.set_text(content)
        except Exception as e:
            self.text_buffer.set_text(f"Binary or unreadable file: {e}")
