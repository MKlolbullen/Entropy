# LNK-NG

A modern desktop evolution of the original LNKUp concept: one window, two persistent views, a clean LNK builder, and a singleton Responder analysis controller.

> Designed for authorized security testing and defensive validation. The bundled Responder controller runs in **Analyze mode only** (`-A`); active poisoning is intentionally not enabled in this initial branch.

## Current UI

### LNK Builder
- Listener host synchronized from the selected network interface
- NTLM / environment shortcut modes
- Environment-variable selection
- Execute-after-open command field
- Output-path chooser
- UNC/icon preview
- Cross-platform `.lnk` generation backend

### Responder
- Interface discovery + IPv4 display
- One persistent `QProcess` owned by a singleton controller
- Analyze-only mode
- Verbose / quiet controls
- Command preview
- Start / stop lifecycle
- Structured, redacted event table
- Switching views does **not** restart Responder

## Architecture

```text
MainWindow
├── ResponderController      # single process owner
├── BuilderView
└── ResponderView

lnkup/
├── core/
│   ├── interfaces.py
│   ├── lnk.py
│   ├── models.py
│   └── validation.py
├── responder/
│   ├── controller.py
│   ├── events.py
│   └── options.py
└── ui/
    ├── builder_view.py
    ├── main_window.py
    └── responder_view.py
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
python generate.py \
  --host 192.168.1.44 \
  --type ntlm \
  --output test.lnk
```

Environment mode:

```bash
python generate.py \
  --host 192.168.1.44 \
  --type environment \
  --vars USERNAME COMPUTERNAME USERDOMAIN \
  --output env.lnk
```

## Roadmap

1. LNK inspector/parser view
2. JSONL run manifests and structured event persistence
3. Preflight diagnostics: ports, privileges, executable/version detection
4. Responder configuration reader and service-state matrix
5. Engagement/run IDs and evidence export
6. Linux + Windows CI
7. Packaging/release workflow

## Provenance

This project is a refactored next-generation experiment inspired by the original `Plazmaz/LNKUp`, with a new architecture and desktop workflow.
