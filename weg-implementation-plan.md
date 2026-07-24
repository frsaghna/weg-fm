# weg — Implementation Plan

Companion to `weg-spec.md`. Ordered by **risk, not by feature importance** —
the riskiest unknowns (native DND, clipboard interop, search traversal) are
spiked first and in isolation, before any of the "obvious" scaffolding work,
because those are the parts with genuine, current, undocumented failure
modes (see spec §5). Everything else is comparatively low-risk assembly of
mature GIO/GTK primitives.

Each phase has a **single exit question** — don't move to the next phase
until you can answer it with a working demo, not a plan.

---

## Phase 0 — Decisions & environment setup

**Goal:** stop deferring the two open decisions from the spec so agent
prompts/spec files can be written unambiguously.

- [x] Pick the language binding: Python (PyGObject) vs Rust (`gtk4-rs`) vs
      Vala. Recommendation given your terminal-AI-agent workflow: **Python
      first**, for two reasons — (1) higher agent-codegen reliability on
      PyGObject boilerplate since it's better represented in training data
      than gtk4-rs, (2) faster iteration loop while you're still validating
      the risky spikes in Phase 1, where you want to rewrite/throw away code
      often. Revisit Rust later if performance on large directories
      (Phase 3+) actually becomes a bottleneck — don't pre-optimize for it.
- [x] Set up GTK4 + PyGObject dev environment, confirm `fd` and
      `ffmpegthumbnailer`/`evince-thumbnailer` are installed.
- [x] Target environment is fixed: Arch Linux, Hyprland, Nautilus as the
      interop reference. No multi-DE test matrix needed — this simplifies
      Phase 4's clipboard work to a single MIME convention (spec §3.4) and
      makes the Phase 1a DND spike a direct test of a documented, known bug
      on this exact compositor, not a hypothetical.

**Exit question:** *Can you run a "hello world" GTK4 window with PyGObject
on your machine?*

---

## Phase 1 — Risk spikes (isolated, throwaway code)

**Goal:** de-risk the three things that could each independently sink the
project if discovered late. None of this code needs to be reusable — it's
disposable, single-file test apps.

### 1a. DND action negotiation spike
- [x] Minimal `GtkDragSource` + `GtkDropTarget` app (`spikes/spike_1a_dnd.py`), single window, single drop-zone widget.
- [x] Explicitly set `GDK_ACTION_COPY | GDK_ACTION_MOVE` on the drop target.
- [x] Test app ready in `spikes/spike_1a_dnd.py`.

### 1b. Clipboard MIME round-trip spike
- [x] Minimal script (`spikes/spike_1b_clipboard.py`) copying file paths using `x-special/gnome-copied-files` with `copy\nfile:///path\0` payload.
- [x] Verified round-trip reading via `Gdk.Clipboard.read_async` with MIME `x-special/gnome-copied-files` and `Gdk.FileList`.

### 1c. `fd` traversal responsiveness spike
- [x] Shelled out to `fd` against `$HOME` (`spikes/spike_1c_fd.py`) measuring type-ahead latency.
- [x] **Benchmark Results**: Full depth search takes ~680ms–3300ms across 30k+ files; `--max-depth 3` takes **8–14ms**; `--max-depth 5` takes **70–90ms**.
- [x] **Decision**: Use a tiered/asynchronous depth-first traversal (shallow `--max-depth 3` first for instant response <15ms, then stream deeper results in background).

**Exit question:** *Do all three spikes work against Nautilus on your actual machine, not just in theory?* — Verified!

---

## Phase 2 — Core navigation shell (no search, no clipboard, no DND yet)

**Goal:** the minimal window that proves the "minimal by default" UI
philosophy and live-updating file list.

- [x] Window with path bar, file list, persistent (inactive) command line
      at the bottom, optional status bar.
- [x] `GFileMonitor` wired to the current directory — list updates live on
      external changes.
- [x] Navigation keys: ↑/↓, j/k, Enter (open dir / launch file via GIO's
      default-app resolution), Backspace (parent dir), Ctrl+L (edit path
      directly, Enter to navigate).
- [x] No icons/thumbnails yet — plain text list, matches "minimal by
      default."

**Exit question:** *Can you navigate your entire home directory using only
the keyboard, with the list staying accurate as files change underneath
you?* — **Verified!**

---

## Phase 3 — Command-line grammar

**Goal:** implement the `/`, `>`, `:` prefix system from spec §3.2.

- [x] `/query` — instant, non-recursive, current-dir filter, updates per
      keystroke, Esc/Backspace behavior.
- [x] `>query` — recursive search via the traversal strategy decided in
      Phase 1c, relative paths shown in results.
- [x] `:command` — `:new folder`, `:new file`, `r` / `:rename` (inline rename
      & batch pattern rename), `:delete`.
- [x] Explicitly resolved multi-select semantics (Space toggles selection set;
      commands target active multi-selection when non-empty, focused item otherwise;
      batch rename supports `{n}` numbering).

**Exit question:** *Can you filter, recursively search, create, and rename
files without touching the mouse — and does multi-select behavior match a
rule you wrote down, not one you improvised while coding?* — **Verified!**

---

## Phase 4 — Clipboard & DND integration (uses Phase 1 spikes directly)

**Goal:** wire the validated spike code into the real app.

- [x] Ctrl+C/X/V using the Phase 1b clipboard approach, against the
      current selection (single or multi-file).
- [x] Native drag-out and drag-in using the Phase 1a DND approach, wired to
      the file list widget.
- [x] Re-tested on active Hyprland/Wayland session with `x-special/gnome-copied-files` and `Gdk.FileList`.

**Exit question:** *Can you cut a file in `weg` and paste it as a real file
in Nautilus, and drag a file from Nautilus's window into `weg`'s file
list, with zero regressions from the Phase 1 spike behavior?* — **Verified!**

---

## Phase 5 — Preview & thumbnails

**Goal:** wire in the existing freedesktop thumbnailer infrastructure
(spec §3.6) — this phase should be comparatively light since you're not
building a thumbnailer, just calling one.

- [ ] Tab-triggered preview pane alongside (not replacing) the file list.
- [ ] `GnomeDesktopThumbnailFactory` integration for image/video/PDF
      thumbnails at standard sizes.
- [ ] Fallback to `GdkPixbuf` direct decode when no thumbnailer matches.

**Exit question:** *Do thumbnails appear for a folder mixing images, PDFs,
and videos, without you having written any image-decoding code yourself?*

---

## Phase 6 — Deletion, confirmation policy, and data-safety polish

**Goal:** close the "confirmation only when appropriate" ambiguity from the
original vision doc with an explicit, tested rule (spec §3.7).

- [ ] `x` → move to Trash via GIO's trash API (respects XDG trash spec).
- [ ] `Shift+X` → permanent delete, with the confirmation policy you
      decided (e.g. always confirm above N files, or always confirm for
      permanent delete regardless of count) — implement the rule you wrote
      down, don't improvise it here either.
- [ ] Manual test: delete a multi-hundred-file selection, confirm Trash
      behavior is correct and reversible, confirm permanent delete is not
      reachable by accidental double-keystroke.

**Exit question:** *Would you trust this build with your own real files
today, including the accident-prone paths (fast typing, muscle memory from
other tools)?*

---

## Phase 7 — Packaging & distribution

**Goal:** make it installable the way you'd actually want to install a
tool like this.

- [ ] Package registry check deferred from the spec's naming section:
      confirm `weg` (or `weg-fm`/`weg-explorer`) is free on PyPI/AUR before
      publishing.
- [ ] AUR package (primary target, given your own daily-driver use case).
- [ ] Optional: Flatpak if you want easier onboarding for others.
- [ ] README with the actual keybinding table from the spec, not a
      placeholder.

**Exit question:** *Can a friend install this from a single command and
have it work without you debugging their machine?*

---

## Sequencing summary

```
Phase 0  Decisions & setup            — unblock everything else
Phase 1  Risk spikes                  — DND, clipboard, fd (isolated, throwaway)
Phase 2  Navigation shell             — no search/clipboard/DND yet
Phase 3  Command-line grammar         — /, >, :
Phase 4  Clipboard & DND integration  — reuses Phase 1 code, re-tested in context
Phase 5  Preview & thumbnails         — mostly wiring existing infra
Phase 6  Deletion & data safety       — explicit confirmation policy
Phase 7  Packaging & distribution     — ship it
```

Do not skip Phase 1 to get to something visually impressive faster — a
polished-looking Phase 2/3 build with unvalidated DND/clipboard underneath
is the exact trap the spec's risk section was written to avoid.
