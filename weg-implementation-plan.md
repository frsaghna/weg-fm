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

- [ ] Pick the language binding: Python (PyGObject) vs Rust (`gtk4-rs`) vs
      Vala. Recommendation given your terminal-AI-agent workflow: **Python
      first**, for two reasons — (1) higher agent-codegen reliability on
      PyGObject boilerplate since it's better represented in training data
      than gtk4-rs, (2) faster iteration loop while you're still validating
      the risky spikes in Phase 1, where you want to rewrite/throw away code
      often. Revisit Rust later if performance on large directories
      (Phase 3+) actually becomes a bottleneck — don't pre-optimize for it.
- [ ] Set up GTK4 + PyGObject dev environment, confirm `fd` and
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
- Minimal `GtkDragSource` + `GtkDropTarget` app, single window, single
  drop-zone widget.
- Explicitly set `GDK_ACTION_COPY | GDK_ACTION_MOVE` on the drop target
  (not copy-only — this is the exact documented bug: Nautilus offers "move"
  as its drag action, and a copy-only `GtkDropTarget` gets silently
  rejected during Wayland DnD negotiation, so `enter` never fires).
- Test on your actual Hyprland session, dragging **from Nautilus into your
  app**, and **from your app into Nautilus**. Both directions must work —
  this is the one spike where "works in theory" isn't good enough, since
  the known bug report is specifically Wayland/Hyprland + Nautilus, i.e.
  your exact setup.
- If it fails silently (no `enter` signal firing), debug via
  `WAYLAND_DEBUG=1` and inspect the action bitmask being offered/accepted.

### 1b. Clipboard MIME round-trip spike
- Minimal script: copy a file path onto the clipboard using
  `x-special/gnome-copied-files` with the `copy\nfile:///path\0` payload.
- Test: paste into Nautilus — must appear as an actual file paste
  (Ctrl+V creates a copy), not a pasted text string.
- Test the reverse: copy a file in Nautilus, read it back from the
  clipboard in your script, confirm you get the file path(s), not
  plain text.
- No need to branch on `$XDG_CURRENT_DESKTOP` or handle KDE/MATE MIME
  variants — Nautilus is the fixed target, so `x-special/gnome-copied-files`
  is the only convention this needs to support.

### 1c. `fd` traversal responsiveness spike
- Shell out to `fd` against your actual `$HOME` (real size, not a toy
  directory) and measure latency for a live type-ahead-style query
  (`>proj`-style partial match).
- Compare subjective feel against a breadth-first alternative if the
  depth-first result feels slow for near-root files (spec §5, item 3).
- Decide: `fd` as-is, `fd` with `--max-depth` tiers, or a different
  traversal tool. This is a one-line config decision, but only after
  testing on real data — don't guess.

**Exit question:** *Do all three spikes work against Nautilus on your
actual machine, not just in theory?* If any fails, that failure defines
real scope for Phase 4/5 — don't proceed assuming it'll "probably be fine
once integrated."

---

## Phase 2 — Core navigation shell (no search, no clipboard, no DND yet)

**Goal:** the minimal window that proves the "minimal by default" UI
philosophy and live-updating file list.

- [ ] Window with path bar, file list, persistent (inactive) command line
      at the bottom, optional status bar.
- [ ] `GFileMonitor` wired to the current directory — list updates live on
      external changes (create a file in another terminal, confirm it
      appears without manual refresh).
- [ ] Navigation keys: ↑/↓, j/k, Enter (open dir / launch file via GIO's
      default-app resolution), Backspace (parent dir), Ctrl+L (edit path
      directly, Enter to navigate).
- [ ] No icons/thumbnails yet — plain text list, matches "minimal by
      default."

**Exit question:** *Can you navigate your entire home directory using only
the keyboard, with the list staying accurate as files change underneath
you?*

---

## Phase 3 — Command-line grammar

**Goal:** implement the `/`, `>`, `:` prefix system from spec §3.2.

- [ ] `/query` — instant, non-recursive, current-dir filter, updates per
      keystroke, Esc/Backspace behavior.
- [ ] `>query` — recursive search via the traversal strategy decided in
      Phase 1c, relative paths shown in results.
- [ ] `:command` — start with the simplest commands first: `:new folder`,
      `:new file`, `r` for inline rename (no dialog).
- [ ] Explicitly resolve (don't defer again) the multi-select semantics
      question from spec §3.3: what does `:rename` do with 5 files
      selected? Decide and document before implementing `:delete`/
      `:compress` for multi-select, since they inherit the same ambiguity.

**Exit question:** *Can you filter, recursively search, create, and rename
files without touching the mouse — and does multi-select behavior match a
rule you wrote down, not one you improvised while coding?*

---

## Phase 4 — Clipboard & DND integration (uses Phase 1 spikes directly)

**Goal:** wire the validated spike code into the real app, not re-derive it.

- [ ] Ctrl+C/X/V using the Phase 1b clipboard approach, against the
      current selection (single or multi-file).
- [ ] Native drag-out and drag-in using the Phase 1a DND approach, wired to
      the file list widget instead of a placeholder drop-zone.
- [ ] Re-test against Nautilus on your actual Hyprland session after
      integration — the spike working in isolation doesn't guarantee it
      survives being embedded in the full widget tree (event controller
      ordering, focus handling).

**Exit question:** *Can you cut a file in `weg` and paste it as a real file
in Nautilus, and drag a file from Nautilus's window into `weg`'s file
list, with zero regressions from the Phase 1 spike behavior?*

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

## Phase 8 — Next features (do not start until Phase 6 is actually closed)

**Gate:** this phase is explicitly blocked on Phase 6's open items — multi-select
semantics (spec §3.3) and the delete confirmation policy (spec §3.7) — being
decided and implemented, not just discussed. Adding new features on top of
undecided data-safety rules is how "confirmation only when appropriate"
turns into a real incident. Also blocked on the outstanding preview bug
(binary files rendering as garbled text — check content-type before
choosing a preview path, don't rely on decode-failure fallback).

Priority order below reflects effort-vs-value, not just interest.

### 8.1 Full multi-level undo/redo
Not a single-level "last operation" undo — a real stack, following the
pattern both Nautilus and Dolphin already ship as a standard (not
add-on) feature, so this is proven territory, not a research problem.

**Architecture — copy the pattern that actually works in practice, not a
generic diff/snapshot stack:**
- One dedicated undo-record type per operation kind (rename, move, copy,
  trash), each storing exactly the state needed to reverse *that specific
  operation* — not a single generic "before/after path" abstraction.
- Rename records must track old *and* new display name explicitly, not
  just a path pair — Nautilus shipped a real bug fix for exactly this,
  because path-only tracking silently broke undo on backends where the
  simple before/after reference wasn't sufficient to reliably reverse a
  rename. Don't relearn that the hard way; build the richer record from
  the start.
- Move records track old/new parent + name. Trash records track the
  original location so restore-from-trash is exact.
- Each undo attempt should re-validate its record's preconditions still
  hold (target still exists, hasn't been touched externally) before
  acting — given `GFileMonitor` is already wired up and Nautilus/DND
  interop is confirmed working, external changes between stack entries
  are a real, not theoretical, scenario for this project specifically.

**Explicit scope boundary:** permanent delete (`Shift+X`) stays outside
the undo system entirely — this isn't a gap to close, it's the same wall
Nautilus and Dolphin hit. Their answer wasn't a technical fix, it was UI
discouragement: make Trash (`x`) the default, reversible path, and keep
permanent delete a deliberately separate, harder-to-reach action. That's
consistent with — and reinforces — the Phase 6 confirmation-policy
decision rather than replacing it.

**Also worth noting as a differentiator:** `nnn`/`ranger`, the tools this
project draws lineage from, don't ship real undo — reversibility there is
plugin-based move-to-trash with manual restore. Full undo/redo would be a
genuine capability gain over the terminal-FM tradition, not just parity
with GUI tools.

### 8.2 Directory history
Alt+←/→ (or similar) back/forward through recently visited directories,
browser-style. Cheap — reuses navigation events you already emit.

### 8.3 Frecency-based quick jump
A `~`/`@`-style prefix (à la `zoxide`) to jump to a frequently/recently
visited directory by typing a fragment of its name. Strong fit for the
"intent first" philosophy; likely the single most-missed feature for
anyone used to `zoxide`-augmented shells.

### 8.4 Fuzzy matching for `/` and `>`
Upgrade from plain substring filtering to fuzzy/subsequence matching with
basic scoring. Pure algorithm swap on the existing search paths — no new
UI surface.

---

### Weigh against "minimal by default" before building

### 8.5 Pattern-based batch rename
Sed-style find/replace or numbered-sequence renaming for multi-select.
**Explicitly depends on 8's gate above** — don't build this before
multi-select semantics are decided, or the ambiguity gets encoded into the
UI instead of resolved.

### 8.6 On-demand directory size
A `:du`-style command, deliberately opt-in — never compute sizes eagerly
for visible entries, since that would violate the "instantaneous
navigation" goal for large directories.

### 8.7 Git status badges
Inline modified/untracked indicators. High personal value, but this is the
first feature that pulls `weg` from "generic file explorer" toward "dev
tool" — a real philosophy fork, not a neutral addition. Decide
deliberately rather than drifting into it.

---

### Explicitly optional / low priority

### 8.8 User-configurable keybindings
Dotfile-driven remapping. Speculative investment while you're the only
user — revisit if/when someone else actually wants different bindings.

### 8.9 Archive extraction
Counterpart to the existing `:compress`. Low risk, not urgent.

---

## Phase 9 — Reliability hardening (symlinks, permissions, scale) [COMPLETED]

**Why this phase exists:** Phase 8 closed out cleanly, including catching
and fixing several genuine edge cases (batch rename undo atomicity,
chained/cyclic renames, mid-batch rollback) that weren't in the original
spec — proof that undocumented edge cases keep surfacing as real bugs, not
hypotheticals. This phase gets ahead of three more categories before they
show up the same way: as a bug found in daily use rather than a decision
made deliberately.

### 9.1 Symlink handling [COMPLETED]
Given the dev-heavy daily workflow (node_modules, symlinked dotfiles),
this is common-case territory, not an edge case. Decisions locked in:

- **Trash/permanent delete**: Deletes/unlinks the link pointer itself (`os.unlink` / `NOFOLLOW_SYMLINKS`), never following it or modifying target contents.
- **Move/copy**: Copies/moves the link node (`follow_symlinks=False` / `symlinks=True`), preserving symlinks cleanly across paste/drag operations.
- **Navigate/enter**: Following into a symlinked directory is supported and safe.
- **Recursive search (`>`)**: Confirmed `fd` is executed without `-L` (no-follow symlinks).
- **Broken symlinks**: Rendered as visually distinct (`🔗! name -> target [broken]`), without crashing on `stat` or vanishing from the list.
- **Display**: Visual marker distinguishing symlinks (`🔗 name -> target`) with cyan italic styling (`.symlink-item`).

### 9.2 Permission-denied directories [COMPLETED]
- Catches `GLib.Error` / permission errors from `enumerate_children`, rendering an inline `"Permission denied"` state (`[Permission Denied or Unreadable Directory]`) with status bar error message.
- Handled race case gracefully if directory gets deleted or permission-changed.
- Per-file stat failures within readable directory render placeholders (`? B` size/date) without throwing or breaking list rendering.

### 9.3 Large-directory stress test [COMPLETED]
- Confirmed non-blocking directory listing with `NOFOLLOW_SYMLINKS` and background thread / idle queue loading.
- Confirmed lazy thumbnail generation for visible preview pane items only.
- Confirmed `fd` search performance against large directories.

**Exit question:** *Can you navigate, delete, and search inside a
symlink-heavy, 50k+-file directory you don't have full read permission
across, without a single crash or silently wrong behavior?* **YES.**

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
Phase 8  Next features                — gated on Phase 6 actually closing
Phase 9  Reliability hardening        — symlinks, permissions, scale
```

Do not skip Phase 1 to get to something visually impressive faster — a
polished-looking Phase 2/3 build with unvalidated DND/clipboard underneath
is the exact trap the spec's risk section was written to avoid.
