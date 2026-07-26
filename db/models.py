"""
SQLAlchemy ORM models for CLPTM database.
"""

from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from db.session import Base


class Player(Base):
    """Player feature dataset model matching data/processed/feature_dataset.csv."""
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core identity & metadata
    player = Column(String(255), nullable=False, index=True)
    team = Column(String(255), nullable=True)
    league = Column(String(255), nullable=False, index=True)
    position = Column(String(50), nullable=True)
    position_primary = Column(String(50), nullable=True)
    age = Column(Float, nullable=True)
    minutes = Column(Float, nullable=True)

    # Counting stats
    goals = Column(Float, nullable=True)
    assists = Column(Float, nullable=True)
    xg = Column(Float, nullable=True)
    xag = Column(Float, nullable=True)
    npxg = Column(Float, nullable=True)
    prog_carries = Column(Float, nullable=True)
    prog_passes = Column(Float, nullable=True)
    prog_receptions = Column(Float, nullable=True)
    key_passes = Column(Float, nullable=True)
    xa = Column(Float, nullable=True)
    tackles_won = Column(Float, nullable=True)
    interceptions = Column(Float, nullable=True)
    clearances = Column(Float, nullable=True)
    carries = Column(Float, nullable=True)
    touches = Column(Float, nullable=True)

    # Per 90 metrics
    shots_p90 = Column(Float, nullable=True)
    shots_on_target_p90 = Column(Float, nullable=True)
    goals_p90 = Column(Float, nullable=True)
    assists_p90 = Column(Float, nullable=True)
    xg_p90 = Column(Float, nullable=True)
    xag_p90 = Column(Float, nullable=True)
    npxg_p90 = Column(Float, nullable=True)
    prog_carries_p90 = Column(Float, nullable=True)
    prog_passes_p90 = Column(Float, nullable=True)
    prog_receptions_p90 = Column(Float, nullable=True)
    key_passes_p90 = Column(Float, nullable=True)
    xa_p90 = Column(Float, nullable=True)
    tackles_won_p90 = Column(Float, nullable=True)
    interceptions_p90 = Column(Float, nullable=True)
    clearances_p90 = Column(Float, nullable=True)
    carries_p90 = Column(Float, nullable=True)
    touches_p90 = Column(Float, nullable=True)
    pass_completion_pct = Column(Float, nullable=True)

    # Z-scores
    goals_zscore = Column(Float, nullable=True)
    assists_zscore = Column(Float, nullable=True)
    xg_zscore = Column(Float, nullable=True)
    xag_zscore = Column(Float, nullable=True)
    npxg_zscore = Column(Float, nullable=True)
    prog_carries_zscore = Column(Float, nullable=True)
    prog_passes_zscore = Column(Float, nullable=True)
    prog_receptions_zscore = Column(Float, nullable=True)
    key_passes_zscore = Column(Float, nullable=True)
    xa_zscore = Column(Float, nullable=True)
    tackles_won_zscore = Column(Float, nullable=True)
    interceptions_zscore = Column(Float, nullable=True)
    clearances_zscore = Column(Float, nullable=True)
    carries_zscore = Column(Float, nullable=True)
    touches_zscore = Column(Float, nullable=True)
    shots_zscore = Column(Float, nullable=True)
    shots_on_target_zscore = Column(Float, nullable=True)
    pass_completion_zscore = Column(Float, nullable=True)

    # League & strength factors
    league_lsc = Column(Float, nullable=True)
    lsc_adj_goals_p90 = Column(Float, nullable=True)
    lsc_adj_assists_p90 = Column(Float, nullable=True)
    lsc_adj_xg_p90 = Column(Float, nullable=True)
    lsc_adj_xag_p90 = Column(Float, nullable=True)
    lsc_adj_npxg_p90 = Column(Float, nullable=True)
    lsc_adj_shots_p90 = Column(Float, nullable=True)
    lsc_adj_shots_on_target_p90 = Column(Float, nullable=True)
    lsc_adj_prog_carries_p90 = Column(Float, nullable=True)
    lsc_adj_prog_passes_p90 = Column(Float, nullable=True)
    lsc_adj_prog_receptions_p90 = Column(Float, nullable=True)
    lsc_adj_key_passes_p90 = Column(Float, nullable=True)
    lsc_adj_xa_p90 = Column(Float, nullable=True)
    lsc_adj_carries_p90 = Column(Float, nullable=True)
    lsc_adj_touches_p90 = Column(Float, nullable=True)
    lsc_adj_tackles_won_p90 = Column(Float, nullable=True)
    lsc_adj_interceptions_p90 = Column(Float, nullable=True)
    lsc_adj_clearances_p90 = Column(Float, nullable=True)
    team_strength_ratio = Column(Float, nullable=True)
    poss_adj_touches_p90 = Column(Float, nullable=True)

    # Position flags & play style metrics
    pos_gk = Column(Integer, nullable=True)
    pos_df = Column(Integer, nullable=True)
    pos_mf = Column(Integer, nullable=True)
    pos_fw = Column(Integer, nullable=True)
    age_curve_score = Column(Float, nullable=True)
    play_style_progressive = Column(Float, nullable=True)
    play_style_direct_carry = Column(Float, nullable=True)
    play_style_defensive = Column(Float, nullable=True)

    # Percentiles
    shots_p90_pct = Column(Float, nullable=True)
    shots_on_target_p90_pct = Column(Float, nullable=True)
    goals_p90_pct = Column(Float, nullable=True)
    assists_p90_pct = Column(Float, nullable=True)
    xg_p90_pct = Column(Float, nullable=True)
    xag_p90_pct = Column(Float, nullable=True)
    npxg_p90_pct = Column(Float, nullable=True)
    prog_carries_p90_pct = Column(Float, nullable=True)
    prog_passes_p90_pct = Column(Float, nullable=True)
    prog_receptions_p90_pct = Column(Float, nullable=True)
    key_passes_p90_pct = Column(Float, nullable=True)
    xa_p90_pct = Column(Float, nullable=True)
    tackles_won_p90_pct = Column(Float, nullable=True)
    interceptions_p90_pct = Column(Float, nullable=True)
    clearances_p90_pct = Column(Float, nullable=True)
    carries_p90_pct = Column(Float, nullable=True)
    touches_p90_pct = Column(Float, nullable=True)
    poss_adj_touches_p90_pct = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("player", "league", name="uq_player_league"),
    )
