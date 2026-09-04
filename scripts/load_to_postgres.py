"""
Ingestion script to load data/processed/feature_dataset.csv into the relational database.
Populates all 8 tables defined in TransferPred_Schema.sql and db/models.py:
  1. League
  2. Team
  3. User (default accounts: admin, viewer)
  4. Player
  5. PlayerStats
  6. PlayerStyleProfile
  7. TransferPrediction
  8. ScenarioSimulation
"""

import sys
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.session import engine, SessionLocal, Base
from db.models import League, Team, User, Player, PlayerStats, PlayerStyleProfile
from api.auth import hash_password
from src.utils import load_config, resolve_path

LEAGUE_METADATA = {
    "Premier League": {"lsc": 1.00, "country": "England"},
    "Bundesliga":     {"lsc": 0.88, "country": "Germany"},
    "La Liga":        {"lsc": 0.93, "country": "Spain"},
    "Serie A":        {"lsc": 0.88, "country": "Italy"},
    "Ligue 1":        {"lsc": 0.82, "country": "France"},
}


def load_dataset_to_db():
    cfg = load_config()
    csv_path = resolve_path(cfg, "processed_data", "feature_dataset.csv")
    if not csv_path.exists():
        raise FileNotFoundError(f"Feature dataset CSV not found at {csv_path}")

    print(f"Reading CSV from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows from CSV.")

    # Deduplicate on natural key (player, league), keeping highest minutes entry
    if "minutes" in df.columns:
        df = df.sort_values("minutes", ascending=False)
    df = df.drop_duplicates(subset=["player", "league"], keep="first")
    print(f"Unique (player, league) records to process: {len(df)}")

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    dialect_name = engine.dialect.name
    print(f"Target database dialect: {dialect_name}")

    try:
        # ── 1. Seed Leagues ──────────────────────────────────────────────────
        league_id_map = {}
        for lg_name, meta in LEAGUE_METADATA.items():
            existing = session.query(League).filter(League.league_name == lg_name).first()
            if not existing:
                existing = League(
                    league_name=lg_name,
                    lsc_coefficient=meta["lsc"],
                    country=meta["country"],
                )
                session.add(existing)
                session.flush()
            league_id_map[lg_name] = existing.league_id
        print(f"Seeded {len(league_id_map)} leagues.")

        # ── 2. Seed Teams ────────────────────────────────────────────────────
        team_id_map = {}
        team_groups = (
            df.groupby(["team", "league"])["team_strength_ratio"]
            .mean()
            .reset_index()
        )
        for _, row in team_groups.iterrows():
            tm_name = str(row["team"])
            lg_name = str(row["league"])
            lg_id = league_id_map.get(lg_name)
            if not lg_id:
                continue
            str_ratio = float(row["team_strength_ratio"]) if pd.notna(row["team_strength_ratio"]) else 1.0

            existing = session.query(Team).filter(
                Team.team_name == tm_name,
                Team.league_id == lg_id,
            ).first()
            if not existing:
                existing = Team(
                    team_name=tm_name,
                    league_id=lg_id,
                    team_strength_ratio=str_ratio,
                )
                session.add(existing)
                session.flush()
            else:
                existing.team_strength_ratio = str_ratio
            team_id_map[(tm_name, lg_id)] = existing.team_id
        print(f"Seeded {len(team_id_map)} teams.")

        # ── 3. Seed Users ────────────────────────────────────────────────────
        default_users = [
            ("viewer", "viewer123", "viewer"),
            ("admin", "admin123", "admin"),
        ]
        for uname, pwd, role in default_users:
            u = session.query(User).filter(User.username == uname).first()
            if not u:
                u = User(username=uname, hashed_password=hash_password(pwd), role=role)
                session.add(u)
        session.flush()
        print("Seeded default users (admin, viewer).")

        # ── 4. Seed Players, Stats, and Style Profiles ────────────────────────
        players_to_insert = []
        stats_to_insert = []
        profiles_to_insert = []

        for _, r in df.iterrows():
            lg_id = league_id_map.get(r["league"])
            if not lg_id:
                continue
            tm_id = team_id_map.get((r["team"], lg_id))

            p = session.query(Player).filter(
                Player.player_name == r["player"],
                Player.league_id == lg_id,
            ).first()

            age_val = float(r["age"]) if pd.notna(r.get("age")) else None
            mins_val = float(r["minutes"]) if pd.notna(r.get("minutes")) else 0.0

            if not p:
                p = Player(
                    player_name=r["player"],
                    position=str(r.get("position", "")),
                    position_primary=str(r.get("position_primary", "")),
                    age=age_val,
                    team_id=tm_id,
                    league_id=lg_id,
                    team=str(r.get("team", "")),
                    league=str(r.get("league", "")),
                    minutes=mins_val,
                )
                session.add(p)
                session.flush()
            else:
                p.age = age_val
                p.minutes = mins_val
                p.team_id = tm_id
                p.team = str(r.get("team", ""))
                p.position = str(r.get("position", ""))

            # Stats
            ps = session.query(PlayerStats).filter(PlayerStats.player_id == p.player_id).first()
            if not ps:
                ps = PlayerStats(
                    player_id=p.player_id,
                    minutes=mins_val,
                    goals=float(r.get("goals", 0)),
                    assists=float(r.get("assists", 0)),
                    xg=float(r.get("xg", 0)),
                    xag=float(r.get("xag", 0)),
                    goals_p90=float(r.get("goals_p90", 0)),
                    assists_p90=float(r.get("assists_p90", 0)),
                    xg_p90=float(r.get("xg_p90", 0)),
                    xag_p90=float(r.get("xag_p90", 0)),
                    prog_passes_p90=float(r.get("prog_passes_p90", 0)),
                    prog_carries_p90=float(r.get("prog_carries_p90", 0)),
                    key_passes_p90=float(r.get("key_passes_p90", 0)),
                    pass_completion_pct=float(r.get("pass_completion_pct", 0)),
                    lsc_adj_goals_p90=float(r.get("lsc_adj_goals_p90", 0)),
                    lsc_adj_xg_p90=float(r.get("lsc_adj_xg_p90", 0)),
                )
                session.add(ps)

            # Style profile
            psp = session.query(PlayerStyleProfile).filter(PlayerStyleProfile.player_id == p.player_id).first()
            if not psp:
                psp = PlayerStyleProfile(
                    player_id=p.player_id,
                    age_curve_score=float(r.get("age_curve_score", 0)),
                    play_style_progressive=float(r.get("play_style_progressive", 0)),
                    play_style_direct_carry=float(r.get("play_style_direct_carry", 0)),
                    play_style_defensive=float(r.get("play_style_defensive", 0)),
                    poss_adj_touches_p90=float(r.get("poss_adj_touches_p90", 0)),
                )
                session.add(psp)

        session.commit()
        print(f"Successfully committed all relational entities into database ({dialect_name}).")
    except Exception as e:
        session.rollback()
        print(f"Error loading dataset into DB: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    load_dataset_to_db()
