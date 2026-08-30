# LNK-NG

A modern desktop evolution of the original LNKUp concept: **one window, two persistent views**, a clean LNK builder/inspector, and a singleton Responder analysis controller.

> Built for authorized security testing, lab validation, and defensive analysis. Responder execution remains **Analyze mode only** (`-A`) in Phase 2; the service matrix is deliberately read-only.

## Phase 2

### LNK Builder → Build / Inspect

The first primary view now contains two workflows without adding another top-level screen:

- **Build** — listener synchronization, NTLM/environment modes, command/output configuration, UNC preview and `.lnk` generation.
- **Inspect** — validate the Shell Link header, inspect target/arguments/workdir/icon metadata, enumerate UNC references and extract useful embedded strings. On Windows it uses `win32com`; on Linux it attempts `pylnk3` and falls back to binary forensic extraction.

### Responder → Preflight / Services / Events

Responder remains one persistent `QProcess`, but the view now adds:

- executable resolution and version detection
- automatic `Responder.conf` discovery
- privilege/elevation check
- known listener-port conflict detection
- read-only service-state matrix parsed from `Responder.conf`
- structured per-run evidence directories
- JSON manifest + JSONL event stream
- visible run/session ID
- credential/hash-like values redacted before UI/event persistence

## Evidence model

Every analysis start creates:

```text
runs/
└── 20260830T081500Z-a1b2c3d4/
    ├── manifest.json
    └── events.jsonl
```

`manifest.json` records the mode, interface, command, executable, timestamps and exit result. `events.jsonl` receives the redacted structured event stream.

## Architecture

```text
MainWindow
├── LNK Builder
│   ├── Build
│   └── Inspect
│
└── Responder
    ├── Preflight
    ├── Services (read-only)
    └── Events

ResponderController
├── QProcess (single owner)
└── RunStore
    ├── manifest.json
    └── events.jsonl
```

## Install

### Linux / Kali

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[linux,dev]'
lnk-ng
```

### Windows

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e "[windows,dev]"
lnk-ng
```

Responder is an external dependency and must be available in `PATH`, or its executable path can be entered in the UI.

## CLI compatibility

```bash
python generate.py --host 192.168.1.44 --type ntlm --output test.lnk
```

Environment mode:

```bash
python generate.py \
  --host 192.168.1.44 \
  --type environment \
  --vars USERNAME COMPUTERNAME USERDOMAIN \
  --output env.lnk
```

## Safety boundary

LNK-NG Phase 2 can inspect the installed Responder configuration and show which services are configured, but does **not** edit `Responder.conf` and does **not** expose active poisoning mode. This keeps the orchestration layer deterministic while the preflight, evidence, parser, and UX pieces mature.

## Next

- richer protocol-aware event parsing
- evidence/export browser
- link-property risk indicators in Inspector
- CI across Linux + Windows
- packaged releases
- optional engagement metadata and scoped allowlists

## Provenance

LNK-NG is a refactored next-generation experiment inspired by the original `Plazmaz/LNKUp`, with a new architecture and desktop workflow.
