"""
SQLAlchemy ORM models for CLPTM database.
Matches the StarUML relational architecture and TransferPred_Schema.sql.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship, synonym
from db.session import Base


class League(Base):
    """League entity with LSC translation coefficients."""
    __tablename__ = "League"

    league_id = Column(Integer, primary_key=True, autoincrement=True)
    league_name = Column(String(255), unique=True, nullable=False, index=True)
    lsc_coefficient = Column(Float, nullable=False, default=1.0)
    country = Column(String(100), nullable=True)

    teams = relationship("Team", back_populates="league_rel", cascade="all, delete-orphan")
    players = relationship("Player", back_populates="league_rel", foreign_keys="Player.league_id")


class Team(Base):
    """Team entity with calculated relative strength ratios."""
    __tablename__ = "Team"

    team_id = Column(Integer, primary_key=True, autoincrement=True)
    team_name = Column(String(255), nullable=False, index=True)
    league_id = Column(Integer, ForeignKey("League.league_id", ondelete="CASCADE"), nullable=False)
    team_strength_ratio = Column(Float, default=1.0)

    league_rel = relationship("League", back_populates="teams")
    players = relationship("Player", back_populates="team_rel")


class User(Base):
    """User account entity for role-based API access."""
    __tablename__ = "User"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")

    predictions = relationship("TransferPrediction", back_populates="user_rel")


class Player(Base):
    """Player core entity linking to team and league."""
    __tablename__ = "Player"

    player_id = Column(Integer, primary_key=True, autoincrement=True)
    player_name = Column(String(255), nullable=False, index=True)
    position = Column(String(50), nullable=True)
    position_primary = Column(String(50), nullable=True)
    age = Column(Float, nullable=True)
    team_id = Column(Integer, ForeignKey("Team.team_id", ondelete="SET NULL"), nullable=True)
    league_id = Column(Integer, ForeignKey("League.league_id", ondelete="CASCADE"), nullable=False)

    # Convenience/denormalized fields for backward compatibility and fast search
    player = synonym("player_name")
    team = Column(String(255), nullable=True)
    league = Column(String(255), nullable=True, index=True)
    minutes = Column(Float, nullable=True)

    # Relationships
    team_rel = relationship("Team", back_populates="players")
    league_rel = relationship("League", back_populates="players", foreign_keys=[league_id])
    stats = relationship("PlayerStats", back_populates="player_rel", uselist=False, cascade="all, delete-orphan")
    style_profile = relationship("PlayerStyleProfile", back_populates="player_rel", uselist=False, cascade="all, delete-orphan")
    predictions = relationship("TransferPrediction", back_populates="player_rel", cascade="all, delete-orphan")


class PlayerStats(Base):
    """Detailed season statistics per player."""
    __tablename__ = "PlayerStats"

    stats_id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("Player.player_id", ondelete="CASCADE"), unique=True, nullable=False)
    minutes = Column(Float, nullable=True)
    goals = Column(Float, nullable=True)
    assists = Column(Float, nullable=True)
    xg = Column(Float, nullable=True)
    xag = Column(Float, nullable=True)
    goals_p90 = Column(Float, nullable=True)
    assists_p90 = Column(Float, nullable=True)
    xg_p90 = Column(Float, nullable=True)
    xag_p90 = Column(Float, nullable=True)
    prog_passes_p90 = Column(Float, nullable=True)
    prog_carries_p90 = Column(Float, nullable=True)
    key_passes_p90 = Column(Float, nullable=True)
    pass_completion_pct = Column(Float, nullable=True)
    lsc_adj_goals_p90 = Column(Float, nullable=True)
    lsc_adj_xg_p90 = Column(Float, nullable=True)

    player_rel = relationship("Player", back_populates="stats")


class PlayerStyleProfile(Base):
    """Engineered tactical and stylistic profile scores."""
    __tablename__ = "PlayerStyleProfile"

    profile_id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("Player.player_id", ondelete="CASCADE"), unique=True, nullable=False)
    age_curve_score = Column(Float, nullable=True)
    play_style_progressive = Column(Float, nullable=True)
    play_style_direct_carry = Column(Float, nullable=True)
    play_style_defensive = Column(Float, nullable=True)
    poss_adj_touches_p90 = Column(Float, nullable=True)

    player_rel = relationship("Player", back_populates="style_profile")


class TransferPrediction(Base):
    """Audited transfer performance prediction history."""
    __tablename__ = "TransferPrediction"

    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("Player.player_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("User.user_id", ondelete="SET NULL"), nullable=True)
    source_league_id = Column(Integer, ForeignKey("League.league_id"), nullable=False)
    target_league_id = Column(Integer, ForeignKey("League.league_id"), nullable=False)
    projected_goals_p90 = Column(Float, nullable=True)
    projected_assists_p90 = Column(Float, nullable=True)
    projected_xg_p90 = Column(Float, nullable=True)
    ci_low_goals = Column(Float, nullable=True)
    ci_high_goals = Column(Float, nullable=True)
    adaptation_score_pct = Column(Float, nullable=True)
    risk_score_pct = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    player_rel = relationship("Player", back_populates="predictions")
    user_rel = relationship("User", back_populates="predictions")
    source_league = relationship("League", foreign_keys=[source_league_id])
    target_league = relationship("League", foreign_keys=[target_league_id])
    simulations = relationship("ScenarioSimulation", back_populates="prediction_rel", cascade="all, delete-orphan")


class ScenarioSimulation(Base):
    """Counterfactual scenario simulation records."""
    __tablename__ = "ScenarioSimulation"

    simulation_id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(Integer, ForeignKey("TransferPrediction.prediction_id", ondelete="CASCADE"), nullable=False)
    feature_name = Column(String(100), nullable=False)
    feature_val_simulated = Column(Float, nullable=False)
    simulated_target_val = Column(Float, nullable=False)

    prediction_rel = relationship("TransferPrediction", back_populates="simulations")
