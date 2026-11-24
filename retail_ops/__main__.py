import argparse
from pathlib import Path
from .core import ROOT, build_database, write_report

p = argparse.ArgumentParser(description="Build the retail operations analysis")
p.add_argument("--data", type=Path, default=ROOT / "data")
p.add_argument("--output", type=Path, default=ROOT / "reports")
a = p.parse_args()
with build_database(a.data) as connection:
    r = write_report(connection, a.output)
print(f"Created report for {r['period_days']} days and {len(r['stores'])} stores: {a.output / 'dashboard.html'}")
