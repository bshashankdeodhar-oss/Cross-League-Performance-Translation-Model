"""
report.py — Phase 6: Human-readable report renderer.

Takes output from predict.py and formats it as a clean markdown report.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def render_report(result: dict) -> str:
    """
    Format a prediction result dict into a readable markdown report.

    Parameters
    ----------
    result : dict
        Output of predict_player().

    Returns
    -------
    str: formatted report string
    """
    player = result.get("player", "Unknown")
    source = result.get("source_league", "?")
    target = result.get("target_league", "?")
    src_lsc = result.get("source_lsc", "?")
    tgt_lsc = result.get("target_lsc", "?")

    g90  = result.get("projected_goals_p90")
    a90  = result.get("projected_assists_p90")
    xg90 = result.get("projected_xg_p90")
    xag90= result.get("projected_xag_p90")
    ci_lo= result.get("ci_low_goals")
    ci_hi= result.get("ci_high_goals")
    mins = result.get("minutes_expectation")
    adapt= result.get("adaptation_score_pct")
    risk = result.get("risk_score_pct")
    factors = result.get("top_5_factors", [])

    pos = str(result.get("position", result.get("position_primary", "MF"))).upper()

    # Progression & Defensive projected metrics
    prog_passes = result.get("projected_prog_passes_p90")
    key_passes  = result.get("projected_key_passes_p90")
    prog_carries= result.get("projected_prog_carries_p90")
    tackles     = result.get("projected_tackles_won_p90")
    interceptions=result.get("projected_interceptions_p90")
    clearances  = result.get("projected_clearances_p90")

    def fmt(v):
        if v is None:
            return "N/A"
        return f"{v:.3f}"

    def pct(v):
        if v is None:
            return "N/A"
        return f"{v:.1f}%"

    tgt_team = result.get("target_team")
    tgt_team_str = result.get("target_team_strength_ratio")

    report_lines = [
        "=" * 60,
        f"  CLPTM — Transfer Performance Projection",
        "=" * 60,
        f"",
        f"  Player        : {player} ({pos})",
        f"  Transfer      : {source}  →  {target}" + (f" ({tgt_team})" if tgt_team else ""),
        f"  League Diff   : LSC {src_lsc:.2f} → {tgt_lsc:.2f}",
    ]
    if tgt_team:
        report_lines.append(f"  Target Team   : {tgt_team} (Relative Strength: {tgt_team_str:.2f}x)" if tgt_team_str else f"  Target Team   : {tgt_team}")

    report_lines.extend([
        f"",
        "─" * 60,
    ])

    # ── Role-Tailored Projections ───────────────────────────────────────────
    if "GK" in pos:
        report_lines.extend([
            "  🧤 GOALKEEPING & DISTRIBUTION PROJECTIONS",
            "─" * 60,
            f"  Minutes Expectation  : {int(mins) if mins else 'N/A'} min",
            f"  Team Defense Context : {tgt_team if tgt_team else target} (Strength: {tgt_team_str:.2f}x)" if tgt_team_str else f"  Target Context       : {target}",
            "  Clean Sheet Outlook  : Favorable (Dominant possession & control)" if (tgt_team_str and tgt_team_str > 1.15) else "  Clean Sheet Outlook  : Competitive workload expected",
            "  Note                 : Goalkeepers are evaluated on shot prevention environment,",
            "                         stability, and minutes reliability rather than outfield goals.",
        ])
    elif "DF" in pos and "FW" not in pos:
        report_lines.extend([
            "  🛡️ DEFENSIVE & BUILD-UP PROJECTIONS",
            "─" * 60,
            "  [Defensive Disruption]",
            f"    Tackles Won per 90   : {fmt(tackles)}",
            f"    Interceptions per 90 : {fmt(interceptions)}",
            f"    Clearances per 90    : {fmt(clearances)}",
            "",
            "  [Build-up & Progression]",
            f"    Prog. Passes per 90  : {fmt(prog_passes)}",
            f"    Prog. Carries per 90 : {fmt(prog_carries)}",
            "",
            "  [Attacking Contributions]",
            f"    Goals per 90         : {fmt(g90)}  (Assists: {fmt(a90)})",
            f"  Minutes Expectation    : {int(mins) if mins else 'N/A'} min",
        ])
    elif "MF" in pos:
        report_lines.extend([
            "  🎯 CREATION & PROGRESSION PROJECTIONS",
            "─" * 60,
            "  [Playmaking & Progression]",
            f"    Key Passes per 90    : {fmt(key_passes)}",
            f"    Prog. Passes per 90  : {fmt(prog_passes)}",
            f"    Prog. Carries per 90 : {fmt(prog_carries)}",
            f"    Assists per 90       : {fmt(a90)}  (xAG: {fmt(xag90)})",
            f"    Goals per 90         : {fmt(g90)}  (xG: {fmt(xg90)})",
            "",
            "  [Defensive Workrate & Midfield Disruption]",
            f"    Tackles Won per 90   : {fmt(tackles)}",
            f"    Interceptions per 90 : {fmt(interceptions)}",
            "",
            f"  Minutes Expectation    : {int(mins) if mins else 'N/A'} min",
        ])
    else:
        # Forward / Attacker
        report_lines.extend([
            "  ⚡ ATTACKING & FINISHING PROJECTIONS",
            "─" * 60,
            f"  Goals per 90         : {fmt(g90)}  (95% CI: {fmt(ci_lo)} – {fmt(ci_hi)})",
            f"  Assists per 90       : {fmt(a90)}",
            f"  xG per 90            : {fmt(xg90)}",
            f"  xAG per 90           : {fmt(xag90)}",
            f"  Prog. Carries per 90 : {fmt(prog_carries)}",
            f"  Key Passes per 90    : {fmt(key_passes)}",
            f"  Minutes Expectation  : {int(mins) if mins else 'N/A'} min",
        ])

    # ── Adaptation & Risk ───────────────────────────────────────────────────
    shap_label = result.get("shap_target_label")
    shap_title = f"  🔍 TOP 5 DRIVING FACTORS (Explaining {shap_label})" if shap_label else "  🔍 TOP 5 DRIVING FACTORS"

    report_lines.extend([
        f"",
        "─" * 60,
        "  🎯 ADAPTATION & RISK",
        "─" * 60,
        f"  Adaptation Score : {pct(adapt)}",
        f"  Risk Score       : {pct(risk)}",
        f"",
        "─" * 60,
        shap_title,
        "─" * 60,
    ])

    if factors:
        for i, factor in enumerate(factors, 1):
            direction = "▲" if factor.get("direction") == "positive" else "▼"
            label = factor.get("label", factor.get("feature", "?"))
            shap_val = factor.get("shap_value", 0)
            report_lines.append(f"  {i}. {direction} {label}  (SHAP: {shap_val:+.4f})")
    else:
        report_lines.append("  No SHAP factors available (models may need training).")

    # ── Tactical Fit & Squad Upgrade ──────────────────────────────────────────
    tactical_fit = result.get("tactical_fit")
    if tactical_fit:
        scope = tactical_fit.get("baseline_scope", "Positional Benchmark")
        archetype = tactical_fit.get("tactical_archetype", "Versatile Modern Player")
        compat_score = tactical_fit.get("compatibility_score_pct")
        compat_rating = tactical_fit.get("compatibility_rating", "")
        compat_summary = tactical_fit.get("compatibility_summary", "")
        upgrades = tactical_fit.get("upgrades", [])
        formations = tactical_fit.get("recommended_formations", [])
        instructions = tactical_fit.get("key_instructions", [])

        report_lines.extend([
            "",
            "─" * 60,
            f"  📋 SQUAD UPGRADE & TACTICAL FIT ({tgt_team or target})",
            "─" * 60,
            f"  Tactical Archetype   : {archetype}",
        ])
        if compat_score:
            report_lines.append(f"  System Compatibility : {compat_score:.1f}% ({compat_rating})")
        if compat_summary:
            report_lines.append(f"  Tactical Fit Summary : {compat_summary}")

        report_lines.extend([
            "",
            f"  [Positional Benchmark: {scope}]",
        ])

        for u in upgrades:
            badge = u.get("badge", "◆")
            metric = u.get("metric", "")
            proj_v = u.get("projected", 0.0)
            base_v = u.get("baseline", 0.0)
            pct_c = u.get("pct_change", 0.0)
            status = u.get("status", "")
            sign = "+" if pct_c >= 0 else ""
            report_lines.append(f"    {badge} {metric:<25} : {proj_v:.2f} vs {base_v:.2f} ({sign}{pct_c:.1f}% — {status})")

        if formations:
            report_lines.extend([
                "",
                "  [Recommended Formations & Roles]",
            ])
            for f in formations:
                form_name = f.get("formation", "")
                pos_name = f.get("position", "")
                role_name = f.get("role", "")
                rat = f.get("rationale", "")
                report_lines.append(f"    • {form_name:<17} → {pos_name} ({role_name})")
                if rat:
                    report_lines.append(f"      Rationale: {rat}")

        if instructions:
            report_lines.extend([
                "",
                "  [Tactical Instructions for Manager]",
            ])
            for inst in instructions:
                report_lines.append(f"    - {inst}")

    report_lines += [
        f"",
        "=" * 60,
        "  Generated by CLPTM v1.0 — Cross-League Performance Translation Model",
        "=" * 60,
    ]

    return "\n".join(report_lines)


if __name__ == "__main__":
    # Demo with dummy data
    demo = {
        "player": "Florian Wirtz",
        "source_league": "Bundesliga",
        "target_league": "Premier League",
        "source_lsc": 0.92,
        "target_lsc": 1.00,
        "projected_goals_p90": 0.38,
        "projected_assists_p90": 0.29,
        "projected_xg_p90": 0.35,
        "projected_xag_p90": 0.22,
        "ci_low_goals": 0.21,
        "ci_high_goals": 0.55,
        "minutes_expectation": 2200,
        "adaptation_score_pct": 72.5,
        "risk_score_pct": 18.3,
        "top_5_factors": [
            {"label": "xG per 90 (league-adjusted)", "direction": "positive", "shap_value": 0.082},
            {"label": "Age curve score (peak = 24–28)", "direction": "positive", "shap_value": 0.071},
            {"label": "Team strength (relative to league avg)", "direction": "negative", "shap_value": -0.044},
            {"label": "Progressive passes per 90", "direction": "positive", "shap_value": 0.038},
            {"label": "Source league strength coefficient", "direction": "negative", "shap_value": -0.029},
        ],
    }
    print(render_report(demo))
