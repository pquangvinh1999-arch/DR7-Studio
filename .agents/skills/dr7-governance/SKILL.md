---
name: dr7-governance
description: >-
  Mandatory project constitution (AGENTS.md), session-recovery state tracking (state.json),
  error learning (lerning.md), and Owner atlas-to-animation pipeline memory (skills.md)
  for DR7-Studio (Dragon Ball 2D Mobile 60FPS 2000+ real-time combat on Godot/Rust + Supabase).
  Activate at session start, before processing any Owner atlas, before coding, or after fixing bugs.
---

# DR7-Studio Governance & Workflow Protocol

Compatible with both **Antigravity CLI (`agy`)** and **OpenAI Codex (`codex`)** via root `AGENTS.md` and `.agents/` ⇄ `.agent/`.

## Mandatory Files & Distinction of Roles

1. **`AGENTS.md` (Single Root Constitution — Always Mandatory)**:
   - Zero hallucination/guessing, Pre-Task Clarity Gate, Uploaded Atlas Gate, locked official architecture (**Godot 4 + Rust Core + Supabase** and **`Combined 1-Layer` only** — `layered_3d_depth` prohibited), mandatory 2D component ownership & pocket-first chroma-key technical specs, Engine test loop, and 100% Engine ⇄ Localhost parity.
2. **`state.json` (Always Mandatory — Read on Entry, Update After Every Task)**:
   - Run `./loop.sh status` on session start/reconnect; update after every task.
3. **`skills.md` vs `.agents/skills/*` (Never Confuse!)**:
   - **`skills.md`**: End-to-end DR7-Studio workflow from receiving an Owner's raw atlas image to delivering an Engine-verified, Localhost-synced animation. Starts **EMPTY**; write **only** after Owner confirms Human Test success.
   - **`.agents/skills/*`** (`generate2dsprite`, `video2dsprite`, `generate2dmap`, `generate2dmedia`, `codeart2d`): Low-level technical asset scripts invoked *inside* execution steps.
4. **`lerning.md` (Read Before Coding / Asset Work; Write After Verifying a Bug Fix)**:
   - Consult documented root-cause lessons (`LRN-XXX`) before running pipelines; append new lessons immediately after fixing and verifying any bug.

## Owner repair-loop cap (2026-11-13)

For each unresolved issue, allow at most five analyze→fix→`./loop.sh test` cycles. Record the issue, each attempt, actual exit/log and remaining failure. If attempt5 still fails, stop work on that issue and report evidence and attempted remedies to Owner; do not run attempt6 or hand over a failed result. This replaces unbounded retry instructions. Independent work may continue while the unresolved issue awaits Owner direction.

## Commands

- `./loop.sh status` — Session briefing & file dispatch rules
- `./loop.sh check` — Verify `AGENTS.md`, `state.json`, `skills.md`, `lerning.md`, Engine ⇄ Localhost parity, and animation completeness warnings
- `./loop.sh test` — Full CI/CD checks + Python unit tests + Godot headless tests + Rust `cargo test`
