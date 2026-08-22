# qc-advice — Teamers live competitive analytics

Auto-published snapshots from the team analytics stack (refreshed ~5 min).

## The CLI (for teammates + their Claude Code agents)

    curl -sL https://raw.githubusercontent.com/neldosik/qc-advice/main/qc_cli.py -o qc_cli.py
    python qc_cli.py --help

Commands: advice / learned / knowledge / opponents / standings / games /
problems / heartbeats / export / raw. Stdlib-only, prints JSON. Tries the
LAN dashboard first (freshest), falls back to these snapshots automatically.

## Raw files

* `advice.json` — calibration multiplier, category floors, word signals
* `learned.json` — self-learner knobs (median_cal, q_charge, q_accept)
* `t_knowledge.json` — proven t brackets per policy hash + item description
* `analytics.json` — full bundle: standings, per-game breakdown, opponents,
  drift, earnings, learner heartbeats
