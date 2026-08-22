#!/usr/bin/env python3
"""qc — Teamers competitive-analytics CLI for the Claim-to-Fame tournament.

Single file, stdlib only. Made for teammates (and their Claude Code agents)
who are improving the pricing model: every number our analytics stack knows is
one shell command away.

INSTALL (one line):
    curl -sL https://raw.githubusercontent.com/neldosik/qc-advice/main/qc_cli.py -o qc_cli.py

USAGE:
    python qc_cli.py advice        # calibration multiplier, category floors, word signals
    python qc_cli.py learned       # self-learner knobs (median_cal, q_charge, q_accept)
    python qc_cli.py knowledge     # proven t brackets per policy/item (--grep WORD to filter)
    python qc_cli.py opponents     # per-team strategy profiles + drift
    python qc_cli.py standings     # leaderboard
    python qc_cli.py games         # our per-game net + leak breakdown (--last N)
    python qc_cli.py problems     # biggest current money leaks (last 3 games)
    python qc_cli.py heartbeats    # is the learner alive on the game machine?
    python qc_cli.py export        # the whole bundle in one JSON
    python qc_cli.py raw PATH      # any dashboard endpoint, e.g. raw /api/calibration

Everything prints JSON (agent-friendly). Sources, tried in order:
  1. $DASHBOARD_URL if set
  2. the dashboard on the hackathon LAN (live, freshest)
  3. GitHub snapshots (public, ~5 min stale) — works from anywhere

Force one with --source URL|github.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request

LAN_CANDIDATES = [
    os.environ.get("DASHBOARD_URL"),
    "http://10.94.29.119:5177",
    "http://172.20.10.3:5177",
]
GITHUB = "https://raw.githubusercontent.com/neldosik/qc-advice/main"

# command -> (dashboard endpoint, github snapshot file or None)
COMMANDS = {
    "advice": ("/api/advice", "advice.json"),
    "learned": ("/api/learned", "learned.json"),
    "knowledge": ("/api/t_knowledge", "t_knowledge.json"),
    "opponents": ("/api/export", "analytics.json"),
    "standings": ("/api/export", "analytics.json"),
    "games": ("/api/export", "analytics.json"),
    "problems": ("/api/export", "analytics.json"),
    "heartbeats": ("/api/learner_reports", "analytics.json"),
    "export": ("/api/export", "analytics.json"),
}


def _fetch(url: str, timeout: float = 6.0) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def fetch(endpoint: str, snapshot: str | None, source: str | None) -> tuple[dict, str]:
    if source and source != "github":
        data = _fetch(f"{source.rstrip('/')}{endpoint}", timeout=15)
        if data is not None:
            return data, source
        sys.exit(f"error: {source} did not answer")
    if source != "github":
        for base in LAN_CANDIDATES:
            if not base:
                continue
            data = _fetch(f"{base.rstrip('/')}{endpoint}", timeout=4)
            if data is not None:
                return data, base
    if snapshot:
        data = _fetch(f"{GITHUB}/{snapshot}", timeout=15)
        if data is not None:
            return data, "github (may be ~5 min stale)"
    sys.exit("error: no data source reachable (LAN down and no GitHub snapshot)")


def shape(cmd: str, data: dict, args: list[str]) -> dict | list:
    """Trim the export bundle down to what the command asked for."""
    if cmd == "opponents":
        return {"opponents": data.get("opponents", data),
                "drift": data.get("opponent_drift", [])}
    if cmd == "standings":
        return data.get("standings", data)
    if cmd == "games":
        games = data.get("per_game", data)
        if "--last" in args:
            try:
                games = games[-int(args[args.index("--last") + 1]):]
            except (ValueError, IndexError):
                pass
        return games
    if cmd == "problems":
        return {"our_last3_leaks": data.get("our_last3_leaks", {}),
                "opportunities": (data.get("earnings_last5") or {}).get("opportunities", [])}
    if cmd == "heartbeats":
        return data.get("reports", data.get("learner_heartbeats", data))
    if cmd == "knowledge" and "--grep" in args:
        try:
            needle = args[args.index("--grep") + 1].lower()
            rows = [r for r in data.get("rows", [])
                    if needle in (r.get("description") or "").lower()]
            return {"rows": rows}
        except IndexError:
            pass
    return data


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        sys.exit(__doc__)
    cmd = args[0]

    source = None
    if "--source" in args:
        source = args[args.index("--source") + 1]

    if cmd == "raw":
        if len(args) < 2:
            sys.exit("usage: qc_cli.py raw /api/<endpoint>")
        data, src = fetch(args[1], None, source)
    elif cmd in COMMANDS:
        endpoint, snapshot = COMMANDS[cmd]
        data, src = fetch(endpoint, snapshot, source)
        data = shape(cmd, data, args)
    else:
        sys.exit(f"unknown command {cmd!r} — run with --help")

    print(json.dumps(data, indent=1, ensure_ascii=False))
    print(f"# source: {src}", file=sys.stderr)


if __name__ == "__main__":
    main()
