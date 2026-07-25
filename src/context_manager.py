"""
Multi-Context / Tab State Manager for weg (nnn-style contexts 1-8)
with browser-style directory history (Phase 8.2).
"""

import os

class ContextState:
    def __init__(self, context_id, initial_dir):
        self.id = context_id # 1 to 8
        self.current_dir = os.path.abspath(initial_dir)
        self.selected_paths = set()
        self.show_hidden = False
        self.focused_name = None
        self.history_back = []
        self.history_forward = []

    def push_history(self, new_path):
        new_path = os.path.abspath(new_path)
        if self.current_dir and self.current_dir != new_path:
            self.history_back.append(self.current_dir)
            self.history_forward.clear()
            self.current_dir = new_path

    def go_back(self):
        if not self.history_back:
            return None
        prev_path = self.history_back.pop()
        self.history_forward.append(self.current_dir)
        self.current_dir = prev_path
        return prev_path

    def go_forward(self):
        if not self.history_forward:
            return None
        next_path = self.history_forward.pop()
        self.history_back.append(self.current_dir)
        self.current_dir = next_path
        return next_path

class ContextManager:
    def __init__(self, initial_dir=None, total_contexts=8):
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser("~")
        self.initial_dir = os.path.abspath(initial_dir)
        self.total_contexts = total_contexts
        self.active_id = 1

        self.contexts = {}
        for c_id in range(1, total_contexts + 1):
            self.contexts[c_id] = ContextState(c_id, self.initial_dir)

    def get_active(self):
        return self.contexts[self.active_id]

    def set_active_context(self, context_id):
        if 1 <= context_id <= self.total_contexts:
            self.active_id = context_id
            return self.contexts[context_id]
        return None
