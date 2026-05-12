# BrowserHistoryVisualizer (BHV) — Portfolio Disposition

**Status:** Active (release-branch-as-default) — Python + React
local-first browser history analyzer with Phases 0-3 complete.
**Distinguishing quirk: default branch is `feat/initial-release`,
not `main` or `master`** — `origin/main` is essentially empty
(just an MIT license + an init-branch commit). The substantive
product lives on `feat/initial-release` per the operator's GitHub
default-branch setting.

> Disposition uses strict `origin/feat/initial-release` verification.
> **First session repo with a feature-branch-as-default-branch quirk.**

---

## Verification posture

This repo has **only `origin`** (`saagpatel/BrowserHistoryVisualizer`)
— no `legacy-origin` remote. Clean migration state.

But the canonical-branch shape is different from every other repo
this session:

- **`origin/HEAD` points at `feat/initial-release`**, verified via
  `git ls-remote --symref origin HEAD`
- **`origin/main` has only:** `bb83f15 chore: add MIT license` and
  `caa0d08 chore: initialize main branch`. No README, no product.
- **All substantive product work is on `feat/initial-release`:**
  - `568c98a` feat: complete Browser History Visualizer (Phases 0-3)
  - `6036e0c` chore: merge MIT license into `feat/initial-release`

Reading: the operator started the project on a `feat/initial-release`
branch, set GitHub default to that branch, and never merged back to
`main`. This is unusual and worth flagging — most tooling assumes
`main` (or `master`) is canonical. Anything assuming `origin/main`
will silently target an essentially-empty tree here.

Tree on `origin/feat/initial-release`:
- `backend/` — Python backend (FastAPI-style, per README)
- `frontend/` — React dashboard
- Standard codex-os scaffolding: AGENTS.md, CHANGELOG.md, CLAUDE.md,
  CODE_OF_CONDUCT.md, CONTRIBUTING.md, SECURITY.md, Makefile, LICENSE
- `IMPLEMENTATION-ROADMAP.md`

---

## Current state in one paragraph

BrowserHistoryVisualizer (BHV) is a Python + React local-first tool
that reads Chromium-family browser history files directly (no
cloud), runs an analysis pipeline, and serves a React dashboard. Per
README: multi-browser detection (auto-discovers Chrome, Arc, Brave,
Edge, Vivaldi, Opera, and any Chromium browser under
`~/Library/Application Support`), GitHub-style activity heatmap with
5-level intensity buckets, category breakdown via static allowlist
+ optional Claude AI classification, top-domains ranking, hourly
productivity chart (focus vs distraction minutes), rabbit-hole
detection for multi-domain browsing sessions, date range filtering,
and optional launchd integration for a daily 6 AM background
pipeline. Phases 0-3 are complete on canonical `feat/initial-release`.

For full detail see:
- `README.md` on `origin/feat/initial-release`
- `IMPLEMENTATION-ROADMAP.md`

---

## Why "Active" instead of Release Frozen

Phases 0-3 complete suggests product readiness, but two factors keep
this Active rather than Release Frozen:

1. **The default-branch shape is unresolved.** Either the operator
   intends `feat/initial-release` to become the new `main` (rename
   pending) or `main` is the merge target after first release. In
   either case, a release tag right now would point at an
   unconsolidated branch state.
2. **No release-readiness commit visible.** No `feat(release): ...`
   commits, no `RELEASE_RUNBOOK.md`, no Apple-signing setup. The
   product surface is there but the release pipeline isn't.

This sits one step short of the signing cluster — closer to
"shipped but not packaged" rather than "shipped and ready to sign."

---

## Possible next moves (operator choice)

### Option 1 — Consolidate branches, then join the signing cluster

Required scope:

1. Decide: rename `feat/initial-release` → `main`, OR merge into
   `main` and continue tracking via `main`
2. Wire Apple signing if shipping as `.app` (the README suggests
   local Python + React via terminal — but signing applies if
   later packaged via Tauri or similar)
3. Cut v1.0.0

### Option 2 — Ship as Python + React local tool (no signing)

Polish README install path. Operator runs `pip install` and
`npm install` locally. No notarization needed because there's no
distributable binary; users clone and run.

Estimated effort: ~1 hour (mostly README polish).

### Option 3 — Repackage as desktop app (Tauri/Electron)

The current backend + frontend split could collapse into a Tauri
shell. Bigger refactor.

Estimated effort: ~1 week.

### Option 4 — Self-host cluster member

If the operator intends to run this on a server (less likely for a
"local-first" analyzer reading local browser files), wire `launchd/`
+ `nginx/` like RedditSentimentAnalyzer.

Estimated effort: ~2 hours.

---

## Recommendation (informational)

**Option 1 + Option 2 hybrid** is probably right:

1. **First**, consolidate the default-branch shape — rename
   `feat/initial-release` → `main` so future tooling doesn't trip
   on the quirk. This is a 5-minute GitHub setting change plus a
   local `git fetch && git branch -m`.
2. **Then**, ship as Option 2 (local Python + React) until there's
   demand signal for a packaged binary.

The README is already clear about the local-run posture. The signing
question isn't blocking until the operator wants a one-click install
experience.

---

## Portfolio operating system instructions

| Aspect | Posture |
|---|---|
| Portfolio status | `Active (release-branch-as-default)` |
| Default branch | **`feat/initial-release`** (not `main`) — quirk to flag |
| Review cadence | Reduced — Phases 0-3 are done, decision-time is what's needed |
| Resurface conditions | (a) Operator consolidates default-branch shape, (b) operator picks Option 1/2/3/4 |
| Do **not** auto-add to signing cluster | Until default-branch shape is consolidated and signing is wired |
| Special concern | **`origin/main` is essentially empty.** Any tooling assuming `origin/main` has substantive content fails here. |

---

## Why this row has the "release-branch-as-default" quirk

This is **the third "wrong-default-branch" pattern** discovered in
this session, alongside:

- **Echolocate (R8.5):** `master` is canonical, not `main`
- **TicketDashboard / SmartClipboard (R8.4, R9.5):** no local `main`
  branch exists, only `master` + `codex/*` bootstrap branches
- **BrowserHistoryVisualizer (this row):** default is
  `feat/initial-release`, a feature-branch shape, with `main`
  existing-but-empty

Each variant is a different way the "assume `origin/main`" heuristic
can fail. A future portfolio sweep should explicitly check
`git ls-remote --symref origin HEAD` rather than assume `main`.

---

## Reactivation procedure (for the next code session)

1. **Explicitly read the default branch** via
   `git ls-remote --symref origin HEAD`. Don't assume `main`.
2. Review the local stash (`r10-bhv-stash`) — contains CLAUDE.md
   mods, untracked `.claude/`, `.codex/`, `AGENTS.md`, `data/`.
3. **Decide default-branch consolidation** (rename or merge) before
   any further work.
4. Re-run `pip install -r backend/requirements.txt && cd frontend &&
   npm install && npm run dev` to confirm toolchain.
5. Pick Option 1/2/3/4.

---

## Last known reference

| Field | Value |
|---|---|
| **Default branch** | **`feat/initial-release`** (`origin/HEAD` points here) |
| `origin/feat/initial-release` tip | `35b0c32` chore: add initial CHANGELOG |
| `origin/main` tip | `bb83f15` chore: add MIT license (essentially empty) |
| Last substantive commit | `568c98a` feat: complete Browser History Visualizer (Phases 0-3) |
| Build system | Python (backend) + React (frontend), no monorepo manager visible |
| Phases shipped | 0-3 (`568c98a`) |
| Release scaffolding | **None** — no signing, no runbook, no consolidated default branch |
| Distribution shape | Currently undecided — local Python+React run is the README-documented path |
| External integration | Optional Claude AI for category classification |
| Migration state | **No `legacy-origin` remote** — clean |
| Distinguishing feature | **`feat/initial-release` as the canonical default branch.** First session repo with this shape. |
