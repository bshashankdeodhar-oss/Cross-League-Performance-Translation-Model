"""
utils.py — Shared utilities for the CLPTM pipeline.
Handles config loading, logging setup, and path resolution.
"""

import os
import sys
import logging
import yaml
from pathlib import Path

# ── Project root is always the parent of /src ────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_config(config_path: str | None = None) -> dict:
    """Load the YAML config. Defaults to config/config.yaml."""
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "config.yaml"
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg


def resolve_path(cfg: dict, key: str, filename: str = "") -> Path:
    """Resolve a config path key to an absolute path under PROJECT_ROOT."""
    base = PROJECT_ROOT / cfg["paths"][key]
    base.mkdir(parents=True, exist_ok=True)
    return base / filename if filename else base


def get_logger(name: str, cfg: dict | None = None, level: int = logging.INFO) -> logging.Logger:
    """
    Return a logger that writes to both console and a log file.
    Log file is written to <logs_dir>/<name>.log
    """
    logger = logging.getLogger(name)
    if logger.handlers:          # already configured
        return logger
    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler
    if cfg is not None:
        log_dir = PROJECT_ROOT / cfg["paths"]["logs"]
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_dir / f"{name}.log", encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
