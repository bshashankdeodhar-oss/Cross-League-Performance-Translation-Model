import pandas as pd
import re

test_df = pd.read_csv("data_T5/transfers_2026_2027_test_set.csv")

with open("frontend/src/data/teamCrestMap.js", "r", encoding="utf-8") as f:
    code = f.read()

# Parse TEAM_ESPN_IDS
espn_ids = {}
m = re.search(r"export const TEAM_ESPN_IDS = \{([^}]+(?:\{[^}]+\}[^}]+)*)\};", code)
if m:
    block = m.group(1)
    for line in block.split("\n"):
        line = line.strip()
        if line.startswith("//") or not line: continue
        parts = line.split(":")
        if len(parts) == 2:
            key = parts[0].strip().strip("'\"")
            val = parts[1].strip().rstrip(",").strip()
            try:
                espn_ids[key.lower()] = int(val)
            except:
                pass

# Parse TEAM_ALIASES
aliases = {}
m2 = re.search(r"export const TEAM_ALIASES = \{([^}]+(?:\{[^}]+\}[^}]+)*)\};", code)
if m2:
    block = m2.group(1)
    for line in block.split("\n"):
        line = line.strip()
        if line.startswith("//") or not line: continue
        parts = line.split(":")
        if len(parts) == 2:
            k = parts[0].strip().strip("'\"").lower()
            v = parts[1].strip().rstrip(",").strip().strip("'\"").lower()
            aliases[k] = v

print(f"Parsed {len(espn_ids)} ESPN IDs, {len(aliases)} aliases")

all_teams = set(test_df['moving_from'].dropna().unique()) | set(test_df['moving_to'].dropna().unique())

unresolved = []
resolved = []
for t in sorted(all_teams):
    t_clean = t.strip().lower()
    canonical = aliases.get(t_clean, t_clean)
    if canonical in espn_ids or t_clean in espn_ids:
        resolved.append((t, espn_ids.get(canonical, espn_ids.get(t_clean))))
    else:
        unresolved.append(t)

print(f"Resolved: {len(resolved)} / {len(all_teams)}")
print(f"Unresolved: {len(unresolved)}")
print("Unresolved teams:", unresolved)
