"""
Full Multi-Level Undo/Redo System for weg (Phase 8.1).
Supports operation records for Rename, Move, Copy, and Trash with precondition validation.
"""

import os
import shutil
import gi

gi.require_version('Gio', '2.0')
from gi.repository import Gio

class UndoRecord:
    def undo(self):
        raise NotImplementedError
    
    def redo(self):
        raise NotImplementedError

class RenameRecord(UndoRecord):
    def __init__(self, old_path, new_path):
        self.old_path = os.path.abspath(old_path)
        self.new_path = os.path.abspath(new_path)
        self.old_name = os.path.basename(old_path)
        self.new_name = os.path.basename(new_path)

    def undo(self):
        if not os.path.exists(self.new_path):
            return False, f"Cannot undo rename: '{self.new_name}' no longer exists"
        if os.path.exists(self.old_path):
            return False, f"Cannot undo rename: '{self.old_name}' already exists"
        os.rename(self.new_path, self.old_path)
        return True, f"Undid rename: '{self.new_name}' -> '{self.old_name}'"

    def redo(self):
        if not os.path.exists(self.old_path):
            return False, f"Cannot redo rename: '{self.old_name}' no longer exists"
        if os.path.exists(self.new_path):
            return False, f"Cannot redo rename: '{self.new_name}' already exists"
        os.rename(self.old_path, self.new_path)
        return True, f"Redid rename: '{self.old_name}' -> '{self.new_name}'"

class MoveRecord(UndoRecord):
    def __init__(self, src_path, dest_path):
        self.src_path = os.path.abspath(src_path)
        self.dest_path = os.path.abspath(dest_path)

    def undo(self):
        if not os.path.exists(self.dest_path):
            return False, f"Cannot undo move: '{os.path.basename(self.dest_path)}' no longer exists"
        if os.path.exists(self.src_path):
            return False, f"Cannot undo move: target destination '{os.path.basename(self.src_path)}' already exists"
        shutil.move(self.dest_path, self.src_path)
        return True, f"Undid move: '{os.path.basename(self.dest_path)}' returned"

    def redo(self):
        if not os.path.exists(self.src_path):
            return False, f"Cannot redo move: '{os.path.basename(self.src_path)}' no longer exists"
        if os.path.exists(self.dest_path):
            return False, f"Cannot redo move: '{os.path.basename(self.dest_path)}' already exists"
        shutil.move(self.src_path, self.dest_path)
        return True, f"Redid move: '{os.path.basename(self.src_path)}'"

class CopyRecord(UndoRecord):
    def __init__(self, created_paths, src_paths):
        self.created_paths = [os.path.abspath(p) for p in created_paths]
        self.src_paths = [os.path.abspath(p) for p in src_paths]

    def undo(self):
        removed = 0
        for p in self.created_paths:
            if os.path.exists(p):
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    os.remove(p)
                removed += 1
        return True, f"Undid copy: removed {removed} created item(s)"

    def redo(self):
        created = 0
        for src, dest in zip(self.src_paths, self.created_paths):
            if os.path.exists(src):
                if os.path.isdir(src):
                    shutil.copytree(src, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dest)
                created += 1
        return True, f"Redid copy: restored {created} item(s)"

class TrashRecord(UndoRecord):
    def __init__(self, trashed_items):
        # trashed_items is a list of tuples: (original_path, trash_gio_file)
        self.trashed_items = trashed_items

    def undo(self):
        restored = 0
        for orig_path, trash_gfile in self.trashed_items:
            try:
                # Untrash or copy/move back from trash if possible
                if trash_gfile and os.path.exists(trash_gfile.get_path()):
                    shutil.move(trash_gfile.get_path(), orig_path)
                    restored += 1
            except Exception:
                pass
        if restored > 0:
            return True, f"Undid trash: restored {restored} item(s)"
        return False, "Cannot undo trash: trashed item references expired"

    def redo(self):
        trashed = 0
        for orig_path, _ in self.trashed_items:
            if os.path.exists(orig_path):
                try:
                    gfile = Gio.File.new_for_path(orig_path)
                    gfile.trash(None)
                    trashed += 1
                except Exception:
                    pass
        return True, f"Redid trash: moved {trashed} item(s) to Trash"

class UndoManager:
    def __init__(self, max_depth=50):
        self.max_depth = max_depth
        self.undo_stack = []
        self.redo_stack = []

    def push(self, record):
        self.undo_stack.append(record)
        if len(self.undo_stack) > self.max_depth:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def can_undo(self):
        return len(self.undo_stack) > 0

    def can_redo(self):
        return len(self.redo_stack) > 0

    def undo(self):
        if not self.undo_stack:
            return False, "Nothing to undo"
        record = self.undo_stack.pop()
        ok, msg = record.undo()
        if ok:
            self.redo_stack.append(record)
        else:
            # Re-push record if preconditions failed
            self.undo_stack.append(record)
        return ok, msg

    def redo(self):
        if not self.redo_stack:
            return False, "Nothing to redo"
        record = self.redo_stack.pop()
        ok, msg = record.redo()
        if ok:
            self.undo_stack.append(record)
        else:
            self.redo_stack.append(record)
        return ok, msg
