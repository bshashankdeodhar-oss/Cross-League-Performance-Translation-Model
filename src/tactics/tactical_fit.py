"""
tactical_fit.py — Squad Upgrade, Tactical Fit, and Formation Recommendations.

This module evaluates how much a player improves the target team:
  1. Compares projected player metrics against target team (or league) positional incumbents.
  2. Classifies the player into a modern Tactical Archetype.
  3. Evaluates System Compatibility against the target team's tactical context.
  4. Recommends optimal formations, specific tactical roles, and instructions.
"""

from __future__ import annotations
import pandas as pd
import numpy as np


# Metrics tracked per positional group for squad upgrade analysis
POSITION_METRIC_CONFIG = {
    "DF": [
        ("prog_passes_p90", "Ball Progression", "Prog Passes/90", True),
        ("tackles_won_p90", "Ground Duel Disruption", "Tackles Won/90", True),
        ("interceptions_p90", "Pass Interceptions", "Interceptions/90", True),
        ("clearances_p90", "Box Clearances", "Clearances/90", True),
        ("prog_carries_p90", "Carrying out of Defense", "Prog Carries/90", True),
    ],
    "MF": [
        ("key_passes_p90", "Chances Created", "Key Passes/90", True),
        ("prog_passes_p90", "Ball Progression", "Prog Passes/90", True),
        ("xag_p90", "Expected Assisted Goals", "xAG/90", True),
        ("tackles_won_p90", "Midfield Disruption", "Tackles Won/90", True),
        ("goals_p90", "Direct Goal Output", "Goals/90", True),
    ],
    "FW": [
        ("goals_p90", "Direct Goal Output", "Goals/90", True),
        ("xg_p90", "Expected Goals (xG)", "xG/90", True),
        ("key_passes_p90", "Shot Creation", "Key Passes/90", True),
        ("prog_carries_p90", "Carries into Final 3rd", "Prog Carries/90", True),
        ("xag_p90", "Expected Assisted Goals", "xAG/90", True),
    ],
    "GK": [
        ("clearances_p90", "Sweeper-Keeper Actions", "Clearances/90", True),
        ("touches_p90", "Distribution Involvement", "Touches/90", True),
        ("tackles_won_p90", "Sweeper Interventions", "Tackles Won/90", True),
    ],
}


def _classify_archetype(pos: str, player_row: pd.Series, projections: dict) -> tuple[str, str]:
    """
    Classify the player into a modern tactical archetype based on style and projections.
    """
    pos_upper = pos.upper()

    # Retrieve key stats (from projections first, falling back to player row)
    def _val(k: str) -> float:
        v = projections.get(f"projected_{k}", projections.get(k))
        if v is not None:
            return float(v)
        return float(player_row.get(k, 0.0) or 0.0)

    prog_p = _val("prog_passes_p90")
    prog_c = _val("prog_carries_p90")
    tkl = _val("tackles_won_p90")
    clr = _val("clearances_p90")
    kp = _val("key_passes_p90")
    xag = _val("xag_p90")
    xg = _val("xg_p90")
    gls = _val("goals_p90")
    tch = _val("touches_p90")

    if "GK" in pos_upper:
        if clr >= 0.7 or tch >= 35.0:
            return (
                "Modern Sweeper-Keeper / Active Distributor",
                "Operates comfortably outside the box, acts as an extra passing option in build-up, and sweeps behind high defensive lines.",
            )
        return (
            "Traditional Shot-Stopping Goalkeeper",
            "Specializes in goal-line reflex interventions, commanding the six-yard box, and reliable aerial claim security.",
        )

    if "DF" in pos_upper and "FW" not in pos_upper and "MF" not in pos_upper:
        if prog_p >= 4.5 or prog_c >= 1.0:
            return (
                "Elite Ball-Playing Center-Back / Deep Playmaker",
                "World-class progressive passing range from deep; capable of breaking lines and initiating first-phase attacking transitions.",
            )
        if clr >= 3.5 or tkl >= 1.2:
            return (
                "Defensive Stopper / Penalty-Box Anchor",
                "Dominant physical presence focused on aerial clearances, stopping box entries, and aggressive ground duels.",
            )
        return (
            "Modern Balanced Central Defender",
            "Reliable duel winner with competent distribution and positional awareness in a structured backline.",
        )

    if "MF" in pos_upper and "FW" not in pos_upper:
        if kp >= 2.0 or xag >= 0.22:
            return (
                "Advanced Playmaker / Half-Space Conductor",
                "Elite vision and creative timing between opponent lines; prioritizes opening up tight defensive blocks.",
            )
        if tkl >= 1.0 and prog_p >= 4.0:
            return (
                "Dynamic Box-to-Box Engine / Complete Midfielder",
                "Covers massive ground from box to box, contributing equally to defensive turnover recovery and progressive transition.",
            )
        if tkl >= 1.2 and kp < 1.0:
            return (
                "Defensive Midfield Destroyer / Holding Anchor",
                "Screens the back four, intercepts passing lanes, and disrupts opposition transitions with physical authority.",
            )
        return (
            "Deep-Lying Tempo Controller / Facilitator",
            "Dictates the rhythm of possession, recycling play efficiently with high pass completion and tactical discipline.",
        )

    # Forwards, Wingers, and Attacking Midfield/Forwards (e.g. MF,FW)
    if "FW" in pos_upper or ("MF" in pos_upper and "FW" in pos_upper):
        if gls >= 0.40 or xg >= 0.38:
            return (
                "Clinical Primary Goalscorer / Advanced Striker",
                "Lethal penalty-box movement, clinical first-time finishing, and relentless shot generation.",
            )
        if prog_c >= 2.0 or (kp >= 1.8 and xag >= 0.20):
            return (
                "Dynamic Inside Forward / Half-Space Overloader",
                "Attacks from wide or interior channels with explosive carries, destabilizing defensive blocks through direct take-ons and key passes.",
            )
        if tch >= 45.0 or prog_p >= 4.0:
            return (
                "Complete Linking Forward / Creative No. 10",
                "Drops deep to link midfield and attack, creates overloads in the zone of 14, and facilitates goal-scoring runs.",
            )
        return (
            "Direct Transition Forward / Wide Threat",
            "Thrives attacking transitional space in behind with aggressive off-the-ball runs and counter-attacking threat.",
        )

    return (
        "Versatile Modern Utility Player",
        "Adaptable tactical profile capable of fulfilling multiple functional roles depending on game state.",
    )


def _calculate_system_compatibility(
    archetype: str,
    target_team: str | None,
    target_team_strength: float,
    adaptation_score: float,
) -> tuple[float, str, str]:
    """
    Calculate tactical system compatibility percentage and qualitative statement.
    """
    # Base compatibility tied to adaptation score and team environment
    base = 70.0 + (adaptation_score * 0.2)

    # Adjust based on team strength context
    if target_team_strength >= 1.25:
        # Dominant possession team (Man City, Bayern, Real Madrid)
        if any(term in archetype for term in ["Ball-Playing", "Playmaker", "Conductor", "Sweeper-Keeper", "Inside Forward"]):
            base += 12.0
            summary = "Exceptional tactical synergy with dominant possession football and high territorial occupation."
            rating = "World-Class Fit"
        else:
            base += 4.0
            summary = "Strong tactical fit; player will need to adjust to sustained territorial possession."
            rating = "High Fit"
    elif target_team_strength <= 0.90:
        # Lower-table / direct transition team
        if any(term in archetype for term in ["Stopper", "Destroyer", "Direct Transition", "Box-to-Box"]):
            base += 12.0
            summary = "Superb tactical fit for high-workrate, transition-heavy defensive blocks and vertical counter-attacks."
            rating = "Ideal Fit"
        else:
            base += 2.0
            summary = "Decent fit; high individual quality provides a major technical boost despite lower team possession share."
            rating = "Moderate / Quality Boost"
    else:
        # Competitive mid-table team
        base += 8.0
        summary = "Balanced tactical synergy; easily integrates into standard positional rotations."
        rating = "Strong Fit"

    score = min(98.0, max(55.0, base))
    return round(score, 1), rating, summary


def _recommend_formations_and_roles(
    pos: str, archetype: str, player_row: pd.Series
) -> tuple[list[dict], list[str]]:
    """
    Determine recommended formations, specific roles, and manager instructions.
    """
    pos_upper = pos.upper()

    if "GK" in pos_upper:
        formations = [
            {
                "formation": "4-3-3 / 4-2-3-1",
                "position": "Goalkeeper (GK)",
                "role": "Sweeper-Keeper (Support)",
                "rationale": "High starting position provides security behind an aggressive defensive line.",
            },
            {
                "formation": "3-4-2-1 / 3-5-2",
                "position": "Goalkeeper (GK)",
                "role": "Sweeper-Keeper (Defend)",
                "rationale": "Acts as the central distributor linking to wide wing-backs.",
            },
        ]
        instructions = [
            "Position high outside the box during attacking phases to sweep up long through-balls.",
            "Initiate immediate transitions by targeting wide wing-backs with driven distribution.",
            "Maintain proactive communication to organize zonal set-piece structures.",
        ]

    elif "DF" in pos_upper and "FW" not in pos_upper:
        formations = [
            {
                "formation": "3-4-2-1 / 3-5-2",
                "position": "Left Center-Back (LCB)" if "L" in str(player_row.get("player", "")) else "Central / Wide Center-Back",
                "role": "Ball-Playing Defender (Build-Up / Cover)",
                "rationale": "Unlocks progressive passing lanes through half-spaces with central cover behind.",
            },
            {
                "formation": "4-3-3 / 4-2-3-1",
                "position": "Left/Right Central Defender",
                "role": "Ball-Playing Defender (Defend)",
                "rationale": "Provides a solid duel-winning foundation while breaking opponent midfield lines.",
            },
        ]
        instructions = [
            "Step into the midfield line during phase 1 build-up to create central overloads.",
            "Execute diagonal switches of play when the opponent compacts the central corridor.",
            "Maintain aggressive aerial engagement on defensive set pieces and high balls.",
        ]

    elif "MF" in pos_upper and "FW" not in pos_upper:
        formations = [
            {
                "formation": "4-3-3 / 4-2-3-1",
                "position": "Central Attacking Midfielder / Left No. 8",
                "role": "Advanced Playmaker (Attack)",
                "rationale": "Positions the player between opposition midfield and defensive lines to maximize chance creation.",
            },
            {
                "formation": "3-4-2-1",
                "position": "Left Inside No. 10",
                "role": "Inverted Half-Space Creator",
                "rationale": "Operates in tight interior spaces while the wing-back holds outer width.",
            },
        ]
        instructions = [
            "Demand the ball on the half-turn between opponent midfield and defensive blocks.",
            "Deliver early through-balls into channels for overlapping runners.",
            "Lead the immediate counter-pressing wave within 5 seconds of possession loss.",
        ]

    else:
        # Forwards / Wingers
        formations = [
            {
                "formation": "4-3-3 / 4-2-3-1",
                "position": "Left/Right Inverted Winger or Center Forward",
                "role": "Inside Forward (Attack) / Complete Forward",
                "rationale": "Allows cutting inside onto preferred foot to generate shot volume and combine with advancing midfielders.",
            },
            {
                "formation": "3-4-2-1",
                "position": "Second Striker / Shadow Striker",
                "role": "Creative Shadow Striker",
                "rationale": "Drifts into pockets of space behind the main striker to finish cut-backs.",
            },
        ]
        instructions = [
            "Make blind-side diagonal runs between the opposition center-back and full-back.",
            "Isolate the opponent full-back in 1v1 transitional situations.",
            "Engage in high-intensity counter-pressing on the opponent's deep pivot.",
        ]

    return formations, instructions


def analyze_tactical_fit(
    player_row: pd.Series,
    projections: dict,
    target_team: str | None,
    target_league: str,
    df: pd.DataFrame,
    target_team_strength: float = 1.0,
    adaptation_score: float = 50.0,
) -> dict:
    """
    Comprehensive Squad Upgrade and Tactical Fit Analysis.

    Returns
    -------
    dict with keys:
      - target_team: canonical target team or None
      - baseline_scope: name of the benchmark group
      - upgrades: list of dicts with metric comparison, diff, and upgrade badges
      - tactical_archetype: archetype name
      - archetype_description: archetype summary
      - compatibility_score_pct: 0-100 score
      - compatibility_rating: High / World-Class / Moderate
      - compatibility_summary: 1-sentence synergy explanation
      - recommended_formations: list of dicts with formation, position, role, rationale
      - key_instructions: list of tactical manager instructions
    """
    pos_raw = str(player_row.get("position", player_row.get("position_primary", "MF"))).upper()
    pos_parts = [p.strip() for p in pos_raw.split(",") if p.strip()]
    pos_prim = pos_parts[0] if pos_parts else "MF"

    # ── 1. Determine Positional Baseline ──────────────────────────────────────
    baseline_scope = f"{target_league} {pos_prim} Average"
    incumbents = pd.DataFrame()

    if target_team:
        team_mask = (df["league"].str.lower() == target_league.lower()) & (
            df["team"].str.lower() == target_team.lower()
        )
        team_df = df[team_mask]
        if not team_df.empty:
            pos_mask = team_df["position"].fillna("").str.upper().str.contains(pos_prim)
            incumbents = team_df[pos_mask]
            if not incumbents.empty:
                baseline_scope = f"{target_team} {pos_prim} Baseline"

    # League-wide fallback dataframe for this position in target league
    league_pos_df = df[
        (df["league"].str.lower() == target_league.lower())
        & (df["position"].fillna("").str.upper().str.contains(pos_prim))
    ]

    # ── 2. Compute Upgrade Deltas ─────────────────────────────────────────────
    metric_configs = POSITION_METRIC_CONFIG.get(pos_prim, POSITION_METRIC_CONFIG["MF"])
    upgrades = []

    for col, label, unit, higher_is_better in metric_configs:
        # Retrieve projected value
        proj_val = projections.get(f"projected_{col}", projections.get(col))
        if proj_val is None:
            continue
        proj_val = float(proj_val)

        # Calculate baseline from team incumbents (with smart league fallback if 0)
        baseline_val = 0.0
        if not incumbents.empty and col in incumbents.columns:
            mean_team = float(incumbents[col].fillna(0).mean())
            if mean_team > 0.01:
                baseline_val = mean_team

        # Fallback to league baseline if team baseline was 0 / missing
        if baseline_val <= 0.01 and not league_pos_df.empty and col in league_pos_df.columns:
            mean_lg = float(league_pos_df[col].fillna(0).mean())
            baseline_val = mean_lg

        diff = proj_val - baseline_val
        if baseline_val > 0.001:
            pct_change = (diff / baseline_val) * 100.0
        else:
            pct_change = 100.0 if diff > 0 else 0.0

        # Assign badge & status
        if higher_is_better:
            if pct_change >= 40.0:
                badge = "▲"
                status = "Major Upgrade"
            elif pct_change >= 10.0:
                badge = "▲"
                status = "Noticeable Upgrade"
            elif pct_change >= -10.0:
                badge = "◆"
                status = "Parity / Competitive"
            else:
                badge = "▼"
                status = "Positional Dip"
        else:
            badge = "▲" if diff < 0 else "▼"
            status = "Favorable" if diff < 0 else "Higher Workload"

        upgrades.append({
            "metric": label,
            "unit": unit,
            "projected": round(proj_val, 3),
            "baseline": round(baseline_val, 3),
            "diff": round(diff, 3),
            "pct_change": round(pct_change, 1),
            "badge": badge,
            "status": status,
        })

    # ── 3. Tactical Archetype ─────────────────────────────────────────────────
    archetype, archetype_desc = _classify_archetype(pos_raw, player_row, projections)

    # ── 4. System Compatibility ───────────────────────────────────────────────
    compat_score, compat_rating, compat_summary = _calculate_system_compatibility(
        archetype, target_team, target_team_strength, adaptation_score
    )

    # ── 5. Formations & Roles ─────────────────────────────────────────────────
    formations, instructions = _recommend_formations_and_roles(pos_raw, archetype, player_row)

    return {
        "target_team": target_team,
        "baseline_scope": baseline_scope,
        "upgrades": upgrades,
        "tactical_archetype": archetype,
        "archetype_description": archetype_desc,
        "compatibility_score_pct": compat_score,
        "compatibility_rating": compat_rating,
        "compatibility_summary": compat_summary,
        "recommended_formations": formations,
        "key_instructions": instructions,
    }
