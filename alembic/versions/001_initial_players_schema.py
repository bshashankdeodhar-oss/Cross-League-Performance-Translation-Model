"""initial players schema

Revision ID: 001_initial_players_schema
Revises: 
Create Date: 2026-07-25 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_players_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'players',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('player', sa.String(length=255), nullable=False),
        sa.Column('team', sa.String(length=255), nullable=True),
        sa.Column('league', sa.String(length=255), nullable=False),
        sa.Column('position', sa.String(length=50), nullable=True),
        sa.Column('position_primary', sa.String(length=50), nullable=True),
        sa.Column('age', sa.Float(), nullable=True),
        sa.Column('minutes', sa.Float(), nullable=True),
        sa.Column('goals', sa.Float(), nullable=True),
        sa.Column('assists', sa.Float(), nullable=True),
        sa.Column('xg', sa.Float(), nullable=True),
        sa.Column('xag', sa.Float(), nullable=True),
        sa.Column('npxg', sa.Float(), nullable=True),
        sa.Column('prog_carries', sa.Float(), nullable=True),
        sa.Column('prog_passes', sa.Float(), nullable=True),
        sa.Column('prog_receptions', sa.Float(), nullable=True),
        sa.Column('key_passes', sa.Float(), nullable=True),
        sa.Column('xa', sa.Float(), nullable=True),
        sa.Column('tackles_won', sa.Float(), nullable=True),
        sa.Column('interceptions', sa.Float(), nullable=True),
        sa.Column('clearances', sa.Float(), nullable=True),
        sa.Column('carries', sa.Float(), nullable=True),
        sa.Column('touches', sa.Float(), nullable=True),
        sa.Column('shots_p90', sa.Float(), nullable=True),
        sa.Column('shots_on_target_p90', sa.Float(), nullable=True),
        sa.Column('goals_p90', sa.Float(), nullable=True),
        sa.Column('assists_p90', sa.Float(), nullable=True),
        sa.Column('xg_p90', sa.Float(), nullable=True),
        sa.Column('xag_p90', sa.Float(), nullable=True),
        sa.Column('npxg_p90', sa.Float(), nullable=True),
        sa.Column('prog_carries_p90', sa.Float(), nullable=True),
        sa.Column('prog_passes_p90', sa.Float(), nullable=True),
        sa.Column('prog_receptions_p90', sa.Float(), nullable=True),
        sa.Column('key_passes_p90', sa.Float(), nullable=True),
        sa.Column('xa_p90', sa.Float(), nullable=True),
        sa.Column('tackles_won_p90', sa.Float(), nullable=True),
        sa.Column('interceptions_p90', sa.Float(), nullable=True),
        sa.Column('clearances_p90', sa.Float(), nullable=True),
        sa.Column('carries_p90', sa.Float(), nullable=True),
        sa.Column('touches_p90', sa.Float(), nullable=True),
        sa.Column('pass_completion_pct', sa.Float(), nullable=True),
        sa.Column('goals_zscore', sa.Float(), nullable=True),
        sa.Column('assists_zscore', sa.Float(), nullable=True),
        sa.Column('xg_zscore', sa.Float(), nullable=True),
        sa.Column('xag_zscore', sa.Float(), nullable=True),
        sa.Column('npxg_zscore', sa.Float(), nullable=True),
        sa.Column('prog_carries_zscore', sa.Float(), nullable=True),
        sa.Column('prog_passes_zscore', sa.Float(), nullable=True),
        sa.Column('prog_receptions_zscore', sa.Float(), nullable=True),
        sa.Column('key_passes_zscore', sa.Float(), nullable=True),
        sa.Column('xa_zscore', sa.Float(), nullable=True),
        sa.Column('tackles_won_zscore', sa.Float(), nullable=True),
        sa.Column('interceptions_zscore', sa.Float(), nullable=True),
        sa.Column('clearances_zscore', sa.Float(), nullable=True),
        sa.Column('carries_zscore', sa.Float(), nullable=True),
        sa.Column('touches_zscore', sa.Float(), nullable=True),
        sa.Column('shots_zscore', sa.Float(), nullable=True),
        sa.Column('shots_on_target_zscore', sa.Float(), nullable=True),
        sa.Column('pass_completion_zscore', sa.Float(), nullable=True),
        sa.Column('league_lsc', sa.Float(), nullable=True),
        sa.Column('lsc_adj_goals_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_assists_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_xg_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_xag_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_npxg_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_shots_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_shots_on_target_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_prog_carries_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_prog_passes_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_prog_receptions_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_key_passes_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_xa_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_carries_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_touches_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_tackles_won_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_interceptions_p90', sa.Float(), nullable=True),
        sa.Column('lsc_adj_clearances_p90', sa.Float(), nullable=True),
        sa.Column('team_strength_ratio', sa.Float(), nullable=True),
        sa.Column('poss_adj_touches_p90', sa.Float(), nullable=True),
        sa.Column('pos_gk', sa.Integer(), nullable=True),
        sa.Column('pos_df', sa.Integer(), nullable=True),
        sa.Column('pos_mf', sa.Integer(), nullable=True),
        sa.Column('pos_fw', sa.Integer(), nullable=True),
        sa.Column('age_curve_score', sa.Float(), nullable=True),
        sa.Column('play_style_progressive', sa.Float(), nullable=True),
        sa.Column('play_style_direct_carry', sa.Float(), nullable=True),
        sa.Column('play_style_defensive', sa.Float(), nullable=True),
        sa.Column('shots_p90_pct', sa.Float(), nullable=True),
        sa.Column('shots_on_target_p90_pct', sa.Float(), nullable=True),
        sa.Column('goals_p90_pct', sa.Float(), nullable=True),
        sa.Column('assists_p90_pct', sa.Float(), nullable=True),
        sa.Column('xg_p90_pct', sa.Float(), nullable=True),
        sa.Column('xag_p90_pct', sa.Float(), nullable=True),
        sa.Column('npxg_p90_pct', sa.Float(), nullable=True),
        sa.Column('prog_carries_p90_pct', sa.Float(), nullable=True),
        sa.Column('prog_passes_p90_pct', sa.Float(), nullable=True),
        sa.Column('prog_receptions_p90_pct', sa.Float(), nullable=True),
        sa.Column('key_passes_p90_pct', sa.Float(), nullable=True),
        sa.Column('xa_p90_pct', sa.Float(), nullable=True),
        sa.Column('tackles_won_p90_pct', sa.Float(), nullable=True),
        sa.Column('interceptions_p90_pct', sa.Float(), nullable=True),
        sa.Column('clearances_p90_pct', sa.Float(), nullable=True),
        sa.Column('carries_p90_pct', sa.Float(), nullable=True),
        sa.Column('touches_p90_pct', sa.Float(), nullable=True),
        sa.Column('poss_adj_touches_p90_pct', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('player', 'league', name='uq_player_league')
    )
    op.create_index(op.f('ix_players_player'), 'players', ['player'], unique=False)
    op.create_index(op.f('ix_players_league'), 'players', ['league'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_players_league'), table_name='players')
    op.drop_index(op.f('ix_players_player'), table_name='players')
    op.drop_table('players')
