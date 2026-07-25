# weg

*German: "way / path." Also colloquially "gone, away" — a small pun for a
tool whose whole job is to get you where you're going and get out of the way.*

## 0. Naming

**Name:** `weg`

**Collision check (GitHub/web, checked before committing):**
- No existing file manager, terminal navigation tool, or directory-related
  CLI project found using this name. The only notable hit was `davep/weg`,
  an old, unrelated Norton Guide reader for Windows — different era,
  different domain, no real confusion risk.
- Trade-off accepted knowingly: `weg` is a common German dictionary word,
  which is *why* the collision risk is low (nobody's claimed it as a brand)
  but also means it's close to unsearchable on its own — search results
  will surface the dictionary word before the project. Mitigate later with
  a distinctive tagline/README framing and a less generic repo slug if
  needed (e.g. `weg-explorer` or `weg-fm` as the actual repo name, `weg` as
  the binary name).
- Still needs a direct check against package registries specifically
  (PyPI, crates.io, AUR, npm) before final commitment — web search doesn't
  reliably surface registry-only squatting.

Rejected: `hop` (direct collision with an existing pip-installable terminal
file explorer, `hop-file-browser`, with a similar prefix-command model —
too close to ship under the same name). `kern` (no direct collision, but
reads as "kernel" at a glance on a Linux tool, which actively hurts
discoverability with the target audience).

---

## 1. Project Description

`weg` is a minimal, keyboard-first file explorer for Linux, built on
GTK4/GIO, that combines the speed of `nnn` with real native desktop
integration — clipboard paste into GTK/Qt file managers, native
drag-and-drop, and inline thumbnails — without the plugin-shim workarounds
that terminal file managers rely on (external `dragon` popups, text-only
clipboard copies).

**Why not just use nnn + plugins:** validated separately — plugins get you
~80% there (preview-tui, dragdrop via dragon, .cbcp clipboard) but the
clipboard plugin doesn't produce a real "paste as file" in GTK apps (it
copies plain text, not `x-special/gnome-copied-files`), and the drag plugin
is a separate popup window, not drag-from-the-list. This project closes
those specific gaps natively.

**Scope decision:** Linux-only. No Windows/macOS target. This removes the
majority of the original risk (cross-platform clipboard formats, thumbnailer
infra, native chrome) and is the reason this is feasible as a solo project.

**Fixed target environment:** Arch Linux, Hyprland (wlroots-based Wayland
compositor), Nautilus (GNOME Files) as the reference/interop file manager.
This is not a "supported configurations" list — it's the *only* environment
this needs to work correctly on, which removes the multi-desktop-environment
clipboard/DND branching that would otherwise be needed (see §3.4, §5). It
also makes the DND risk in §5 concrete rather than hypothetical: the
documented March 2026 GTK4 DND action-negotiation bug was reported on this
exact combination (Wayland/Hyprland, dragging from Nautilus).

---

## 2. Design Philosophy (`weg`'s core principles)

- **Intent first** — user expresses intent via keyboard; UI narrows to match.
- **Keyboard-first, mouse-optional** — every primary workflow reachable
  without a mouse; mouse fully supported, never required.
- **Minimal by default** — no sidebar, no ribbon, no toolbar. Path, file
  list, optional status bar, persistent command line. Nothing else.
- **Genuinely native** — clipboard, DND, thumbnails, previews behave exactly
  like Nautilus/Dolphin/Thunar from the perspective of other apps on the
  desktop. Not "good enough," actually interoperable.

---

## 3. Feature Spec

### 3.1 Navigation
| Key | Action |
|---|---|
| ↑/↓, j/k | Move selection |
| Enter | Open file/directory |
| Backspace | Parent directory |
| Ctrl+L | Edit path directly |

Directory contents update live via `GFileMonitor` (inotify-backed) — no
manual refresh, no polling loop.

### 3.2 Command-line grammar (persistent, bottom of window)
- `/query` — instant, non-recursive, current-directory filter. Updates per
  keystroke. Esc exits, Backspace edits.
- `>query` — recursive search via `fd`, relative paths shown. See §5 for
  traversal-strategy caveat.
- `:command` — command mode: `:rename`, `:delete`, `:duplicate`, `:compress`,
  `:new folder`, `:new file`, `:terminal`, `:share`. Accepts arguments
  (`:new folder Assets`).

Prefix model is extensible — future prefixes don't change the interaction
model.

### 3.3 Selection
- Space toggles selection, status bar shows count (`5 selected`).
- `:rename`/`:delete`/etc. operate on the active selection when non-empty;
  single hovered file otherwise.
- **Explicit Multi-File Command Semantics**:
  - **Batch Rename (`:rename` / `r`)**: Uses pattern-based index interpolation `{n}` (e.g. `:rename photo_{n}.jpg` -> `photo_1.jpg`, `photo_2.jpg`), or appends `_<n>.<ext>` fallback to prevent overwrite collisions.
  - **Batch Undo Granularity**: Multi-file `Paste` (`CopyRecord`) and multi-file `Trash` (`TrashRecord`) undo as a single atomic transaction on `u`. Batch renames push sequential per-file records.

### 3.4 Clipboard (native, not text-only)
- `Ctrl+C` / `Ctrl+X` / `Ctrl+V` — real file objects, not paths-as-text.
- Implementation: set clipboard MIME type `x-special/gnome-copied-files`
  with `copy\nfile:///path\0` payload. Since Nautilus is the fixed target
  (not a multi-DE support matrix), this is the only MIME convention that
  needs to be implemented — no `$XDG_CURRENT_DESKTOP` branching or
  KDE/MATE variants needed. If you ever add another DE later, that's a
  small, isolated addition, not a rearchitecture.
- This is the fix for the exact gap nnn's `.cbcp` plugin has (plain text
  only).

### 3.5 Drag and drop
- `GtkDragSource` (out) / `GtkDropTarget` (in), native — no external helper
  window.
- **Known risk, not hypothetical:** GTK's DnD action negotiation
  (copy vs. move) has live, current failure modes — e.g. a March 2026 bug
  where GTK apps offering only "copy" silently reject drags from Nautilus
  because Nautilus offers "move," and the `enter` signal never fires. Must
  explicitly support `GDK_ACTION_COPY | GDK_ACTION_MOVE` and test against
  Nautilus specifically, not assume the API "just works."
- **Action item:** build this as an isolated ~50-line spike app first,
  confirm drag-in-from and drag-out-to Nautilus both work, before wiring it
  into the real app.

### 3.6 Preview / thumbnails
- Tab (configurable) opens preview pane alongside the list, doesn't replace
  navigation context.
- Reuse existing Linux thumbnailer infrastructure rather than reinventing
  it: `GnomeDesktopThumbnailFactory` (libgnome-desktop) matches MIME type to
  `/usr/share/thumbnailers/*.thumbnailer` entries (e.g. `ffmpegthumbnailer`
  for video, `evince-thumbnailer` for PDF), falling back to `GdkPixbuf` for
  direct image decode. Standard sizes: 128×128 (normal), 256×256 (large).
- Do not hand-roll thumbnail generation or caching — this is a solved,
  reusable subsystem.

### 3.7 Rename / delete
- `r` — inline rename, no dialog.
- `x` — move to Trash (via GIO trash API, respects XDG trash spec). Always immediate, zero dialog (fully reversible via `u` or Trash undo).
- `Shift+X` / `:delete` — permanent delete. **Explicit Confirmation Policy**: Always requires interactive confirmation via the custom TUI Delete Confirmation window (which defaults keyboard focus to `Cancel [N]` to prevent accidental enter misclicks).

---

## 4. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| UI toolkit | GTK4 (+ optionally libadwaita for styling) | Native widget set, mature DND/clipboard APIs, first-class GIO integration |
| File I/O & monitoring | GIO (`GFile`, `GFileMonitor`) | inotify-backed live updates, async I/O, uniform local/remote (GVfs) file handling — don't reimplement |
| Recursive search | `fd` (shelled out or via `fd`-compatible traversal) | Fast, ignore-aware, good ergonomics — see §5 for a traversal-strategy caveat to test before committing |
| Thumbnails | `GnomeDesktopThumbnailFactory` / freedesktop thumbnailer spec | Reuses Nautilus's own thumbnail cache and generators |
| Clipboard | Raw `GdkClipboard` with `x-special/gnome-copied-files` (+ DE-specific variants) | Required for real "paste as file" interop — not covered by GTK defaults out of the box |
| Drag and drop | `GtkDragSource` / `GtkDropTarget` | Native; requires explicit copy+move action support (see §3.5) |
| Language | **Undecided — pick one:** | |
| → Python (PyGObject) | Fastest to prototype, good agent-codegen coverage, slower for large dir listings | Good fit if velocity > raw perf |
| → Rust (`gtk4-rs`) | Type-safe GObject bindings, good perf, matches GNOME Commander's own 2.0 rewrite | More setup friction, less agent training-data density for gtk4-rs specifically |
| → Vala | Native GTK/GObject idiom, low-ceremony | Smaller ecosystem, less agent familiarity |
| Reference implementation | [GNOME Commander](https://gitlab.gnome.org/GNOME/gnome-commander) | Actively maintained GTK4 file manager (Rust as of 2.0, May 2026) — worth reading its DND/clipboard handling before writing your own from scratch |

---

## 5. Known Risks / Required Spikes (do these before building the rest)

1. **DND action negotiation with Nautilus on Hyprland/Wayland** — copy/move
   bitmask handling. This is not a generic "some Linux setup somewhere" risk
   — the documented bug (GTK apps offering copy-only silently rejected by
   Nautilus's move-action drag, `enter` never fires) was reported on this
   exact compositor. Spike in isolation (§3.5) against your actual desktop
   before writing anything else.
2. **Clipboard MIME round-trip** — copy in your app, paste in Nautilus, and
   vice versa. Confirm both directions before assuming interop works.
3. **`fd` traversal order for live type-ahead** — `fd` is depth-first;
   breadth-first alternatives found relevant files dramatically faster in
   some benchmarks because commonly-wanted files tend to sit near the root.
   Test `>query` responsiveness against your actual home directory size
   before locking in `fd` as the engine.
4. **Multi-select command semantics** (§3.3) and **delete confirmation
   policy** (§3.7) — both underspecified; resolve as explicit rules, not
   "when appropriate," before implementation.

---

## 6. Explicitly Out of Scope

- Windows/macOS support.
- Other desktop environments / compositors (KDE, XFCE, GNOME Shell/Mutter,
  other wlroots compositors) — Hyprland + Nautilus is the fixed target, not
  a compatibility matrix. Revisit only if there's an actual second user on
  a different setup.
- Network filesystem browsing beyond whatever GVfs gives for free.
- Building a custom thumbnail cache or generator.
- A custom clipboard protocol — must match Nautilus's existing convention,
  not invent one.
