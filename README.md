# LNK-NG

A modern desktop evolution of the original LNKUp concept: **one window, two persistent views**, a LNK builder/inspector, and a singleton Responder **Analyze-mode** telemetry controller.

> For authorized security testing, lab validation, and defensive analysis. LNK-NG does not enable active Responder poisoning in Phase 3.

## Phase 3

Phase 3 turns the Phase 2 prototype into a more complete operator workbench without adding top-level window clutter.

### Protocol-aware event model

Responder output is normalized into structured events:

```text
timestamp
protocol       LLMNR / SMB / HTTP / DNS / SYSTEM / ...
event_type     name_resolution_observed / authentication_observed / request_observed / listener_status / error / log
source         observed IPv4 when available
identity       username when present
name           queried name when present
scope          IN / OUT / UNKNOWN
message        redacted original line
```

Credential/hash-like values are redacted before the event reaches the UI or evidence store.

### Engagement + scope tagging

The Responder view now includes an **Engagement** tab with:

- engagement name
- allowed CIDRs
- excluded CIDRs
- validation/normalization
- immutable scope during an active run

Analyze-mode traffic is not blocked or modified; events are tagged against the engagement snapshot. Exclusions win over allowlists. With no allowlist, sources are tagged `UNKNOWN` rather than pretending they are in scope.

### Evidence browser

The **Evidence** tab can:

- enumerate previous runs from `runs/`
- show engagement name, timestamps, event count, and stored structured events
- browse protocol/type/source/scope/message columns
- export a run as a ZIP containing `manifest.json` and `events.jsonl`

Each run remains self-contained:

```text
runs/<run-id>/
├── manifest.json
└── events.jsonl
```

### Event filtering

Live events can be filtered by:

- protocol
- scope (`IN`, `OUT`, `UNKNOWN`)
- free-text search

### CI + releases

GitHub Actions now includes:

- Linux + Windows test matrix
- Python 3.10 / 3.12 / 3.13
- pytest
- Ruff
- tag-triggered wheel/sdist builds
- GitHub Release artifact upload for tags matching `v*`

## UI structure

```text
LNK-NG
├── LNK Builder
│   ├── Build
│   └── Inspect
│
└── Responder
    ├── Engagement
    ├── Preflight
    ├── Services
    ├── Events
    └── Evidence
```

The Responder process remains owned by one controller, so changing tabs or switching back to LNK Builder does not spawn another process.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[linux,dev]'
lnk-ng
```

Windows:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[windows,dev]"
lnk-ng
```

Responder remains an external dependency.

## Tests

```bash
pytest -q
ruff check lnkup tests
```

## Releases

Create and push a version tag to build GitHub release artifacts:

```bash
git tag v0.3.0
git push origin v0.3.0
```

## Safety boundary

Phase 3 reads Responder configuration and runs Responder with `-A`. It does not mutate `Responder.conf`, enable poisoning switches, or automatically interact with observed hosts.

## Next

Potential Phase 4 work:

- protocol-specific detail panes and event correlation
- run comparison/diffing
- signed evidence manifests / SHA-256 chain-of-custody metadata
- installer/application bundles
- richer LNK static-analysis indicators
- optional project-level engagement templates

## Provenance

LNK-NG is a refactored next-generation experiment inspired by the original `Plazmaz/LNKUp`, with a new architecture and desktop workflow.
