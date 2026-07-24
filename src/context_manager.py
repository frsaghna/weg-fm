"""
Multi-Context / Tab State Manager for weg (nnn-style contexts 1-8).
Each context preserves its own working directory, selection, and view settings.
"""

import os

class ContextState:
    def __init__(self, context_id, initial_dir):
        self.id = context_id # 1 to 8
        self.current_dir = os.path.abspath(initial_dir)
        self.selected_paths = set()
        self.show_hidden = False
        self.focused_name = None

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
