import pandas as pd

df = pd.read_csv("data/processed/feature_dataset.csv")
targets = [
    "Sunderland", "Oviedo", "Pisa", "Paris FC", "Como", "Ipswich",
    "St. Pauli", "Holstein Kiel", "Auxerre", "Angers", "Leganés", "RB Leipzig", "Real Madrid"
]
for t in targets:
    matches = df[df["team"].str.contains(t, case=False, na=False)]
    print(f"{t}: {len(matches)} rows, teams: {matches['team'].unique()}")
