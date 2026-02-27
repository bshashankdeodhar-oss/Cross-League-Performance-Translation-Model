# Cross-League Performance Translation Model (CLPTM)

A production-grade machine learning system that predicts how a football player will perform when transferring between leagues.

---

## Project Structure

```
TransferPred/
├── config/
│   └── config.yaml           # All config: paths, leagues, model params
├── data/
│   ├── raw/                  # Original FBRef CSV and archived data
│   ├── interim/              # Mid-pipeline outputs
│   └── processed/            # Final clean datasets
├── logs/                     # Per-phase transformation logs
├── models/                   # Saved model artifacts (.pkl)
├── evaluation/               # Metrics, plots, backtest results
├── notebooks/                # EDA notebooks
├── src/
│   ├── legacy/               # Archived original scripts
│   ├── data/
│   │   ├── ingest.py         # Load & validate raw data
│   │   ├── standardize.py    # Unified column schema
│   │   ├── normalize.py      # Per-90 normalization
│   │   └── league_strength.py # League Strength Coefficient (LSC)
│   ├── features/
│   │   └── engineer.py       # All feature engineering
│   ├── models/
│   │   ├── train.py          # LightGBM, MLP, Bayesian Ridge
│   │   ├── evaluate.py       # MAE, RMSE, calibration, backtest
│   │   └── adaptation.py     # Adaptation & risk model
│   ├── explainability/
│   │   ├── shap_analysis.py  # SHAP factor extraction
│   │   └── scenario_sim.py   # What-if simulator
│   ├── predict.py            # Unified inference endpoint
│   ├── report.py             # Human-readable report renderer
│   └── pipeline.py           # Orchestrator (run everything here)
├── requirements.txt
└── README.md
```

---

## Setup

```powershell
pip install -r requirements.txt
```

> **Data requirement**: Place `players_data-2024_2025.csv` (FBRef) in `data/raw/`.

---

## Running the Pipeline

### Full pipeline (all phases)
```powershell
python src/pipeline.py
```

### Individual phases
```powershell
python src/pipeline.py --phase ingest
python src/pipeline.py --phase standardize
python src/pipeline.py --phase normalize
python src/pipeline.py --phase lsc
python src/pipeline.py --phase features
python src/pipeline.py --phase train
python src/pipeline.py --phase evaluate
python src/pipeline.py --phase adaptation
python src/pipeline.py --phase shap
```

---

## Making Predictions

```powershell
python src/predict.py --player "Florian Wirtz" --source "Bundesliga" --target "Premier League"
```

**Output:**
```
Player         : Florian Wirtz
Transfer       : Bundesliga → Premier League
League Diff    : LSC 0.92 → 1.00

📊 PROJECTED STATISTICS
  Goals per 90    : 0.342  (95% CI: 0.201 – 0.483)
  Assists per 90  : 0.287
  xG per 90       : 0.318
  xAG per 90      : 0.211
  Minutes expect. : 2142 min

🎯 ADAPTATION & RISK
  Adaptation Score : 72.5%
  Risk Score       : 18.3%

🔍 TOP 5 DRIVING FACTORS
  1. ▲ xG per 90 (league-adjusted)
  2. ▲ Age curve score (peak = 24–28)
  3. ▼ Team strength (relative to league avg)
  4. ▲ Progressive passes per 90
  5. ▼ Source league strength coefficient
```

---

## What-If Scenario Simulation

```powershell
python src/explainability/scenario_sim.py \
  --player "Florian Wirtz" \
  --feature team_strength_ratio \
  --values 0.8 1.0 1.2 1.4 \
  --target goals_p90
```

---

## Pipeline Phases Explained

| Phase | Script | Output |
|---|---|---|
| 1. Ingest | `src/data/ingest.py` | Validated raw DataFrame |
| 2. Standardize | `src/data/standardize.py` | `data/interim/standardized.csv` |
| 3. Normalize | `src/data/normalize.py` | `data/interim/normalized.csv` |
| 4. LSC | `src/data/league_strength.py` | `data/processed/unified_dataset.csv` |
| 5. Features | `src/features/engineer.py` | `data/processed/feature_dataset.csv` |
| 6. Train | `src/models/train.py` | `models/*.pkl` + `evaluation/training_metrics.json` |
| 7. Evaluate | `src/models/evaluate.py` | `evaluation/metrics.json`, `evaluation/backtest_report.csv` |
| 8. Adaptation | `src/models/adaptation.py` | `models/adaptation_model.pkl`, `models/risk_model.pkl` |
| 9. SHAP | `src/explainability/shap_analysis.py` | `evaluation/shap_*.png` |

---

## League Strength Coefficients

| League | LSC |
|---|---|
| Premier League | 1.00 (reference) |
| La Liga | 0.95 |
| Bundesliga | 0.92 |
| Serie A | 0.90 |
| Ligue 1 | 0.85 |

Coefficients are configurable in `config/config.yaml`.

---

## Models

Three models are trained per target variable (`goals_p90`, `assists_p90`, `xg_p90`, `xag_p90`):

- **LightGBM** — Primary predictor
- **MLP** — Captures nonlinear interactions
- **Bayesian Ridge** — Uncertainty quantification (confidence intervals)

---

## Roadmap

- [ ] Add La Liga, Serie A, Ligue 1 data
- [ ] Multi-season temporal modeling
- [ ] Transfer value estimation
- [ ] Squad synergy predictor
- [ ] Web dashboard (Streamlit)
