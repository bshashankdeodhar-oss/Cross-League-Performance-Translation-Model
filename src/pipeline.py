"""
pipeline.py — CLPTM Orchestrator.

Runs all pipeline phases in sequence or individually.
This is the single entrypoint for the full system.

Usage:
  # Run all phases end-to-end
  python src/pipeline.py

  # Run a specific phase only
  python src/pipeline.py --phase ingest
  python src/pipeline.py --phase standardize
  python src/pipeline.py --phase normalize
  python src/pipeline.py --phase lsc
  python src/pipeline.py --phase features
  python src/pipeline.py --phase train
  python src/pipeline.py --phase evaluate
  python src/pipeline.py --phase adaptation
  python src/pipeline.py --phase shap

Phases in order:
  1. ingest       → Load & validate raw FBRef data
  2. standardize  → Unified column schema, league/minutes filter
  3. normalize    → Per-90 metrics, league z-scores
  4. lsc          → League Strength Coefficient adjustment
  5. features     → Feature engineering (team strength, age curve, etc.)
  6. train        → Train LightGBM, MLP, Bayesian Ridge
  7. evaluate     → MAE, RMSE, calibration plots, backtest
  8. adaptation   → Adaptation & risk model training
  9. shap         → SHAP summary plots
"""

import argparse
import sys
import time
from pathlib import Path

# Project root is parent of /src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.utils import load_config, get_logger


def run_phase(phase: str, cfg: dict, log):
    t0 = time.time()
    log.info(f"\n{'='*60}")
    log.info(f"  PHASE: {phase.upper()}")
    log.info(f"{'='*60}")

    if phase == "ingest":
        from src.data.ingest import ingest
        result = ingest(cfg)
        log.info(f"  ✓ Ingested {len(result)} rows")
        return result

    elif phase == "standardize":
        from src.data.ingest import ingest
        from src.data.standardize import standardize
        result = standardize(ingest(cfg), cfg)
        log.info(f"  ✓ Standardized shape: {result.shape}")
        return result

    elif phase == "normalize":
        from src.data.ingest import ingest
        from src.data.standardize import standardize
        from src.data.normalize import normalize
        result = normalize(standardize(ingest(cfg), cfg), cfg)
        log.info(f"  ✓ Normalized shape: {result.shape}")
        return result

    elif phase == "lsc":
        from src.data.ingest import ingest
        from src.data.standardize import standardize
        from src.data.normalize import normalize
        from src.data.league_strength import apply_lsc
        result = apply_lsc(normalize(standardize(ingest(cfg), cfg), cfg), cfg)
        log.info(f"  ✓ LSC-adjusted shape: {result.shape}")
        return result

    elif phase == "features":
        from src.data.ingest import ingest
        from src.data.standardize import standardize
        from src.data.normalize import normalize
        from src.data.league_strength import apply_lsc
        from src.features.engineer import engineer
        result = engineer(
            apply_lsc(normalize(standardize(ingest(cfg), cfg), cfg), cfg), cfg
        )
        log.info(f"  ✓ Feature dataset shape: {result.shape}")
        return result

    elif phase == "train":
        from src.models.train import train
        result = train(cfg)
        log.info(f"  ✓ Training complete. Targets trained: {list(result.keys())}")
        return result

    elif phase == "evaluate":
        from src.models.evaluate import evaluate
        result = evaluate(cfg)
        log.info(f"  ✓ Evaluation complete.")
        return result

    elif phase == "adaptation":
        from src.models.adaptation import train_adaptation
        result = train_adaptation(cfg)
        log.info(f"  ✓ Adaptation model complete.")
        return result

    elif phase == "shap":
        from src.explainability.shap_analysis import generate_shap_summary
        generate_shap_summary(cfg)
        log.info(f"  ✓ SHAP plots generated.")
        return None

    else:
        log.error(f"Unknown phase: '{phase}'")
        return None

    elapsed = time.time() - t0
    log.info(f"  Phase '{phase}' completed in {elapsed:.1f}s")


PHASE_ORDER = ["ingest", "standardize", "normalize", "lsc", "features", "train", "evaluate", "adaptation", "shap"]


def main():
    parser = argparse.ArgumentParser(description="CLPTM Pipeline Orchestrator")
    parser.add_argument(
        "--phase",
        type=str,
        default="all",
        choices=["all"] + PHASE_ORDER,
        help="Phase to run. Default: 'all' (runs everything in sequence).",
    )
    args = parser.parse_args()

    cfg = load_config()
    log = get_logger("pipeline", cfg)
    log.info("╔══════════════════════════════════════════════════════════╗")
    log.info("║   Cross-League Performance Translation Model (CLPTM)    ║")
    log.info("║   v1.0 — Production Pipeline Orchestrator               ║")
    log.info("╚══════════════════════════════════════════════════════════╝")

    phases_to_run = PHASE_ORDER if args.phase == "all" else [args.phase]
    total_start = time.time()

    for phase in phases_to_run:
        try:
            run_phase(phase, cfg, log)
        except Exception as e:
            log.error(f"Phase '{phase}' FAILED: {e}", exc_info=True)
            log.error("Pipeline halted. Fix the error above and re-run.")
            sys.exit(1)

    elapsed = time.time() - total_start
    log.info(f"\n✅ Pipeline complete in {elapsed:.1f}s")
    log.info("Outputs:")
    log.info("  data/interim/standardized.csv")
    log.info("  data/interim/normalized.csv")
    log.info("  data/processed/unified_dataset.csv")
    log.info("  data/processed/feature_dataset.csv")
    log.info("  models/*.pkl")
    log.info("  evaluation/metrics.json")
    log.info("  evaluation/backtest_report.csv")
    log.info("  evaluation/shap_*.png")


if __name__ == "__main__":
    main()
