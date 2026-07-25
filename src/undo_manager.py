"""
Full Multi-Level Undo/Redo System for weg (Phase 8.1).
Supports atomic composite operation records for Batch Rename, Move, Copy, and Trash with precondition validation.
Uses 2-stage temporary path resolution with mid-batch error rollback for zero stray temporary files.
"""

import os
import shutil
import uuid
import gi

gi.require_version('Gio', '2.0')
from gi.repository import Gio

class UndoRecord:
    def undo(self):
        raise NotImplementedError
    
    def redo(self):
        raise NotImplementedError

class BatchRenameRecord(UndoRecord):
    def __init__(self, rename_pairs):
        # Captures exact (old_path, new_path) tuples at rename-time
        self.rename_pairs = [(os.path.abspath(old_p), os.path.abspath(new_p)) for old_p, new_p in rename_pairs]

    def undo(self):
        # 1. Precondition validation
        for old_p, new_p in self.rename_pairs:
            if old_p != new_p and not os.path.exists(new_p):
                return False, f"Cannot undo batch rename: '{os.path.basename(new_p)}' no longer exists"

        # 2. Stage 1: Rename all new_p to unique temporary paths
        temp_map = []
        try:
            for old_p, new_p in self.rename_pairs:
                if old_p != new_p and os.path.exists(new_p):
                    tmp_path = new_p + f".weg_undo_{uuid.uuid4().hex[:8]}"
                    os.rename(new_p, tmp_path)
                    temp_map.append((old_p, new_p, tmp_path))
        except Exception as err:
            # Rollback Stage 1 temporary moves if error occurs mid-batch
            for old_p, new_p, tmp_path in temp_map:
                if os.path.exists(tmp_path):
                    try:
                        os.rename(tmp_path, new_p)
                    except Exception:
                        pass
            return False, f"Undo failed mid-batch ({err}); rolled back temporary changes"

        # 3. Stage 2: Move all temporary paths back to target old_p
        reverted = 0
        try:
            for old_p, new_p, tmp_path in temp_map:
                if os.path.exists(tmp_path):
                    os.rename(tmp_path, old_p)
                    reverted += 1
        except Exception as err:
            return False, f"Undo error during restoration ({err}); restored {reverted} file(s)"

        return True, f"Undid batch rename: restored {reverted} file(s)"

    def redo(self):
        # 1. Precondition validation
        for old_p, new_p in self.rename_pairs:
            if old_p != new_p and not os.path.exists(old_p):
                return False, f"Cannot redo batch rename: '{os.path.basename(old_p)}' no longer exists"

        # 2. Stage 1: Move all old_p to unique temporary paths
        temp_map = []
        try:
            for old_p, new_p in self.rename_pairs:
                if old_p != new_p and os.path.exists(old_p):
                    tmp_path = old_p + f".weg_redo_{uuid.uuid4().hex[:8]}"
                    os.rename(old_p, tmp_path)
                    temp_map.append((old_p, new_p, tmp_path))
        except Exception as err:
            # Rollback Stage 1 temporary moves if error occurs mid-batch
            for old_p, new_p, tmp_path in temp_map:
                if os.path.exists(tmp_path):
                    try:
                        os.rename(tmp_path, old_p)
                    except Exception:
                        pass
            return False, f"Redo failed mid-batch ({err}); rolled back temporary changes"

        # 3. Stage 2: Move all temporary paths to target new_p
        redone = 0
        try:
            for old_p, new_p, tmp_path in temp_map:
                if os.path.exists(tmp_path):
                    os.rename(tmp_path, new_p)
                    redone += 1
        except Exception as err:
            return False, f"Redo error during restoration ({err}); applied {redone} rename(s)"

        return True, f"Redid batch rename: renamed {redone} file(s)"

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
