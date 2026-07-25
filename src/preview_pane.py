"""
Preview pane widget for weg.
Supports text preview for text/code files, image/video thumbnail previews,
and explicit 'No preview available' fallback for binary/unsupported formats.
Captures detailed diagnostic error logs for thumbnail generation failures.
"""

import os
import hashlib
import subprocess
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Gio', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio

def get_file_content_type(path):
    data = None
    try:
        with open(path, 'rb') as f:
            data = f.read(512)
    except Exception:
        pass

    ctype, _ = Gio.content_type_guess(filename=path, data=data)
    return ctype or "application/octet-stream"

def is_previewable_text(path, content_type):
    # Null byte check in header - true text files do not contain null bytes
    try:
        with open(path, 'rb') as f:
            header = f.read(512)
        if b'\x00' in header:
            return False
    except Exception:
        return False

    if Gio.content_type_is_a(content_type, "text/plain") or content_type.startswith("text/"):
        return True

    text_mimes = (
        "application/json",
        "application/javascript",
        "application/typescript",
        "application/xml",
        "application/x-sh",
        "application/x-shellscript",
        "application/x-python",
        "application/x-perl",
        "application/x-ruby",
        "application/x-php",
        "application/yaml",
        "application/toml",
        "application/sql",
        "application/x-desktop",
    )
    if any(Gio.content_type_is_a(content_type, m) for m in text_mimes) or content_type in text_mimes:
        return True

    return False

class PreviewPaneWidget(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_size_request(260, -1)

        self.title_label = Gtk.Label(label="Preview", xalign=0.0)
        self.title_label.set_use_underline(False)
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
        content_type = get_file_content_type(path)

        # Strategy 1: Attempt image / video thumbnail rendering
        pixbuf = self._load_thumbnail_or_pixbuf(path, uri, content_type)
        if pixbuf:
            texture = Gdk.Texture.new_for_pixbuf(pixbuf)
            self.picture.set_paintable(texture)
            self.picture.set_visible(True)
            self.scrolled_text.set_visible(False)
            return

        # Strategy 2: Attempt text preview if content-type is text
        if is_previewable_text(path, content_type):
            self.picture.set_visible(False)
            self.scrolled_text.set_visible(True)
            self._load_text_preview(path)
            return

        # Strategy 3: Binary or unsupported file format -> Explicit "No preview available"
        self.picture.set_visible(False)
        self.scrolled_text.set_visible(True)
        self.text_buffer.set_text("No preview available")

    def clear(self):
        self.current_path = None
        self.picture.set_paintable(None)
        self.picture.set_visible(False)
        self.text_buffer.set_text("")
        self.scrolled_text.set_visible(False)

    def _load_thumbnail_or_pixbuf(self, path, uri, content_type):
        # 1. Direct Pixbuf decode for standard raster images
        if content_type.startswith("image/"):
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 256, 256, True)
                if pixbuf:
                    return pixbuf
            except Exception as e:
                print(f"[Preview] Direct image Pixbuf decode failed for '{path}': {e}")

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
                except Exception as e:
                    print(f"[Preview] Cached thumbnail decode error for '{thumb_path}': {e}")

        # 3. Dynamic Thumbnail Generation for Video / Media (MP4, MKV, AVI, MOV, etc.)
        is_video = content_type.startswith("video/") or path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.m4v', '.wmv'))
        if is_video:
            target_thumb_dir = os.path.join(cache_home, "normal")
            os.makedirs(target_thumb_dir, exist_ok=True)
            target_thumb_path = os.path.join(target_thumb_dir, f"{md5_uri}.png")

            # Execute ffmpegthumbnailer with explicit error logging
            cmd = ["ffmpegthumbnailer", "-i", path, "-o", target_thumb_path, "-s", "256"]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if res.returncode == 0 and os.path.exists(target_thumb_path):
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(target_thumb_path, 256, 256, True)
                    if pixbuf:
                        return pixbuf
                else:
                    err_msg = res.stderr.strip() or res.stdout.strip() or "No output generated"
                    print(f"[Preview] Thumbnail generation failed for video '{path}': exit_code={res.returncode}, error={err_msg}")
            except subprocess.TimeoutExpired:
                print(f"[Preview] Thumbnail generation timed out (10s) for video '{path}'")
            except Exception as e:
                print(f"[Preview] Thumbnail generation subprocess error for '{path}': {e}")

        return None

    def _load_text_preview(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                lines = [f.readline() for _ in range(100)]
                content = "".join(lines)
                self.text_buffer.set_text(content)
        except Exception as e:
            self.text_buffer.set_text("No preview available")
