"""List public repos whose homepage is not monitored in .upptimerc.yml.

Why: the status page claims to cover every product, but nothing compared deployed
homepages with the monitor list (Trace, TimeSlipSearch and others were absent).
Report only by default; --fail-on-missing exits 1 for use as a gate.

Usage:
  gh repo list OWNER --visibility public --limit 200 \
    --json name,homepageUrl,isArchived > repos.json
  python scripts/coverage_audit.py --config .upptimerc.yml --repos repos.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# Hosts that are not a deployed product, so never need a monitor.
IGNORED_HOSTS = {"github.com", "npmjs.com"}


def host_of(url: str) -> str:
    host = urlparse(url.strip()).hostname or ""
    return host.removeprefix("www.").lower()


def monitored_hosts(rc_text: str) -> set[str]:
    """Hosts from `url:` lines in .upptimerc.yml (regex, so no PyYAML needed)."""
    hosts = set()
    for m in re.finditer(r"^\s*(?:-\s*)?url:\s*[\"']?([^\s\"']+)", rc_text, re.MULTILINE):
        h = host_of(m.group(1))
        if h:
            hosts.add(h)
    return hosts


def missing(repos: list[dict], monitored: set[str]) -> list[tuple[str, str]]:
    out = []
    for r in repos:
        if r.get("isArchived") or not r.get("homepageUrl"):
            continue
        h = host_of(r["homepageUrl"])
        if h and h not in monitored and h not in IGNORED_HOSTS:
            out.append((r["name"], h))
    return sorted(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", type=Path, default=Path(".upptimerc.yml"))
    ap.add_argument("--repos", type=Path, required=True)
    ap.add_argument("--fail-on-missing", action="store_true")
    args = ap.parse_args(argv)
    gaps = missing(json.loads(args.repos.read_text()), monitored_hosts(args.config.read_text()))
    if not gaps:
        print("All public homepages are monitored.")
        return 0
    print(f"{len(gaps)} public homepage(s) not in {args.config.name}:")
    for name, host in gaps:
        print(f"- {name}: {host}")
    return 1 if args.fail_on_missing else 0


if __name__ == "__main__":
    sys.exit(main())
