"""
Ingestion script to load data/processed/feature_dataset.csv into PostgreSQL.
Idempotent — uses ON CONFLICT (player, league) DO UPDATE.
"""

import sys
from pathlib import Path
import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from db.session import engine, SessionLocal, Base
from db.models import Player
from src.utils import load_config, resolve_path


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
    print(f"Unique (player, league) records to load: {len(df)}")

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    records = df.to_dict(orient="records")
    dialect_name = engine.dialect.name

    session = SessionLocal()
    try:
        if dialect_name == "postgresql":
            # Native PostgreSQL bulk ON CONFLICT DO UPDATE
            for record in records:
                stmt = pg_insert(Player).values(**record)
                update_cols = {k: v for k, v in record.items() if k not in ["player", "league"]}
                stmt = stmt.on_conflict_do_update(
                    index_elements=["player", "league"],
                    set_=update_cols
                )
                session.execute(stmt)
        else:
            # Fallback for SQLite / generic DBs
            for record in records:
                existing = session.query(Player).filter(
                    Player.player == record["player"],
                    Player.league == record["league"]
                ).first()
                if existing:
                    for k, v in record.items():
                        setattr(existing, k, v)
                else:
                    player_obj = Player(**record)
                    session.add(player_obj)

        session.commit()
        print(f"Successfully processed {len(records)} player records into database ({dialect_name}).")
    except Exception as e:
        session.rollback()
        print(f"Error loading dataset into DB: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    load_dataset_to_db()
