"""Step 14: show what the agent has written down. Reads the shop database; changes nothing."""
import sqlite3
import tomllib
from pathlib import Path

here = Path(__file__).resolve().parent
config = tomllib.loads((here / "business.toml").read_text())
data = here / config["data_dir"]
if not (data / "agent.db").exists():
    raise SystemExit("No database yet. Run python3 lucy.py and send a message first.")
with sqlite3.connect(f"file:{data / 'agent.db'}?mode=ro", uri=True) as db:
    print("Proposals (nothing is ever ordered in this lab):")
    try:
        rows = db.execute("SELECT substr(id,1,8), proposal, amount, status, approved_by IS NOT NULL FROM assistant_orders ORDER BY created").fetchall()
    except sqlite3.OperationalError:
        rows = []
    for short, proposal, amount, status, approved in rows:
        print(f"  {short}  {proposal}  total {amount} cents  {status}{'  (approved by the owner)' if approved else ''}")
    if not rows:
        print("  none yet")
if (data / "sessions.db").exists():
    with sqlite3.connect(f"file:{data / 'sessions.db'}?mode=ro", uri=True) as db:
        count = db.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
    print(f"Conversations Lucy remembers: {count} (one hosted session for each chat)")
