"""
scrape_2026_transfers.py — Scrapes 2026/2027 summer transfer window transactions
across Premier League, La Liga, Serie A, Bundesliga, and Ligue 1.

Matches players against the CLPTM master player dataset (data_T5/big5_player_master_2018_2024.csv)
to construct the 2026/2027 forward-testing and prediction benchmark dataset:
  1. data_T5/transfers_2026_2027_raw.csv (all scraped transfers)
  2. data_T5/transfers_2026_2027_test_set.csv (cross-league transfers enriched with source stats)
"""

import os
import sys
import re
import unicodedata
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_T5_DIR = PROJECT_ROOT / "data_T5"
DATA_T5_DIR.mkdir(exist_ok=True)

# ── URLs for Summer 2026 Transfers ───────────────────────────────────────────
TRANSFER_URLS = {
    "England": "https://en.wikipedia.org/wiki/List_of_English_football_transfers_summer_2026",
    "Italy": "https://en.wikipedia.org/wiki/List_of_Italian_football_transfers_summer_2026",
    "Germany": "https://en.wikipedia.org/wiki/List_of_German_football_transfers_summer_2026",
    "Spain": "https://en.wikipedia.org/wiki/List_of_Spanish_football_transfers_summer_2026",
    "France": "https://en.wikipedia.org/wiki/List_of_French_football_transfers_summer_2026",
}

REQ_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def clean_name(s: str) -> str:
    """Normalize names for fuzzy/key matching."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    return "".join(c for c in s.lower() if c.isalnum())


def build_team_league_map(master_df: pd.DataFrame) -> dict[str, str]:
    """Map team names to their respective league using master dataset."""
    team_map = master_df.groupby("team")["league"].agg(lambda x: x.mode()[0]).to_dict()

    # Common aliases & international additions
    aliases = {
        "Man City": "Premier League",
        "Manchester City": "Premier League",
        "Man Utd": "Premier League",
        "Manchester United": "Premier League",
        "Spurs": "Premier League",
        "Tottenham": "Premier League",
        "Tottenham Hotspur": "Premier League",
        "Arsenal": "Premier League",
        "Chelsea": "Premier League",
        "Liverpool": "Premier League",
        "Aston Villa": "Premier League",
        "Newcastle": "Premier League",
        "Newcastle United": "Premier League",
        "West Ham": "Premier League",
        "West Ham United": "Premier League",
        "Brighton": "Premier League",
        "Wolves": "Premier League",
        "Everton": "Premier League",
        "Bournemouth": "Premier League",
        "Brentford": "Premier League",
        "Fulham": "Premier League",
        "Crystal Palace": "Premier League",
        "Nott'm Forest": "Premier League",
        "Nottingham Forest": "Premier League",
        "Real Madrid": "La Liga",
        "Barcelona": "La Liga",
        "Atlético Madrid": "La Liga",
        "Atletico Madrid": "La Liga",
        "Sevilla": "La Liga",
        "Real Sociedad": "La Liga",
        "Real Betis": "La Liga",
        "Villarreal": "La Liga",
        "Valencia": "La Liga",
        "Athletic Club": "La Liga",
        "Athletic Bilbao": "La Liga",
        "Girona": "La Liga",
        "Inter": "Serie A",
        "Inter Milan": "Serie A",
        "Milan": "Serie A",
        "AC Milan": "Serie A",
        "Juventus": "Serie A",
        "Napoli": "Serie A",
        "Roma": "Serie A",
        "Lazio": "Serie A",
        "Atalanta": "Serie A",
        "Fiorentina": "Serie A",
        "Como": "Serie A",
        "Bayern Munich": "Bundesliga",
        "Bayern": "Bundesliga",
        "Dortmund": "Bundesliga",
        "Borussia Dortmund": "Bundesliga",
        "Leverkusen": "Bundesliga",
        "Bayer Leverkusen": "Bundesliga",
        "RB Leipzig": "Bundesliga",
        "Leipzig": "Bundesliga",
        "Eintracht Frankfurt": "Bundesliga",
        "Frankfurt": "Bundesliga",
        "Stuttgart": "Bundesliga",
        "VfB Stuttgart": "Bundesliga",
        "Wolfsburg": "Bundesliga",
        "M'Gladbach": "Bundesliga",
        "Paris S-G": "Ligue 1",
        "Paris Saint-Germain": "Ligue 1",
        "PSG": "Ligue 1",
        "Marseille": "Ligue 1",
        "Monaco": "Ligue 1",
        "Lyon": "Ligue 1",
        "Lille": "Ligue 1",
        "Rennes": "Ligue 1",
        "Nice": "Ligue 1",
        "Lens": "Ligue 1",
    }
    team_map.update(aliases)
    return team_map


def match_league(club_name: str, team_map: dict[str, str]) -> str:
    """Resolve club name to its primary league."""
    if not club_name or pd.isna(club_name):
        return "Unknown"
    club_name = str(club_name).strip()
    
    if club_name in team_map:
        return team_map[club_name]
    
    # Substring search
    for team, league in team_map.items():
        if team.lower() in club_name.lower() or club_name.lower() in team.lower():
            return league

    return "Other"


def scrape_table_format_a(soup: BeautifulSoup, country: str) -> list[dict]:
    """
    Parse standard transfer tables with headers ['Date', 'Player', 'Moving from', 'Moving to', 'Fee'].
    Typical of England and Italy pages.
    """
    records = []
    tables = soup.find_all("table", {"class": "wikitable"})
    for t in tables:
        rows = t.find_all("tr")
        if not rows:
            continue
        headers = [th.get_text(strip=True).lower() for th in rows[0].find_all("th")]

        name_idx = -1
        from_idx = -1
        to_idx = -1
        fee_idx = -1
        date_idx = -1

        for idx, h in enumerate(headers):
            if "player" in h or "name" in h:
                name_idx = idx
            elif "from" in h:
                from_idx = idx
            elif "to" in h:
                to_idx = idx
            elif "fee" in h:
                fee_idx = idx
            elif "date" in h:
                date_idx = idx

        if name_idx != -1 and from_idx != -1 and to_idx != -1:
            for tr in rows[1:]:
                tds = tr.find_all(["td", "th"])
                if len(tds) > max(name_idx, from_idx, to_idx):
                    raw_player = tds[name_idx].get_text(strip=True)
                    # Clean footnotes like [1]
                    clean_p = re.sub(r"\[.*?\]", "", raw_player).strip()
                    clean_from = re.sub(r"\[.*?\]", "", tds[from_idx].get_text(strip=True)).strip()
                    clean_to = re.sub(r"\[.*?\]", "", tds[to_idx].get_text(strip=True)).strip()
                    fee = re.sub(r"\[.*?\]", "", tds[fee_idx].get_text(strip=True)).strip() if fee_idx != -1 and len(tds) > fee_idx else ""
                    date = tds[date_idx].get_text(strip=True) if date_idx != -1 and len(tds) > date_idx else ""

                    if clean_p:
                        records.append({
                            "player": clean_p,
                            "moving_from": clean_from,
                            "moving_to": clean_to,
                            "fee": fee,
                            "date": date,
                            "register_country": country,
                        })
    return records


def scrape_club_roster_format(soup: BeautifulSoup, country: str) -> list[dict]:
    """
    Parse club-by-club transfer tables (typical of Germany, Spain, France).
    Cells contain pattern: PlayerName (from/to OtherClub) [ref]
    """
    records = []
    tables = soup.find_all("table", {"class": "wikitable"})
    for t in tables:
        heading = t.find_previous(["h2", "h3", "h4"])
        club_name = heading.get_text(strip=True).replace("[edit]", "").strip() if heading else "Unknown"

        for tr in t.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if tds:
                cell_text = tds[-1].get_text(strip=True)
                m = re.match(r"^([^(\[]+)(?:\((.*?)\))?(?:\[.*\])?$", cell_text)
                if m:
                    player_name = m.group(1).strip()
                    transfer_details = m.group(2) if m.group(2) else ""

                    moving_from = "Unknown"
                    moving_to = "Unknown"

                    if "from" in transfer_details.lower():
                        moving_to = club_name
                        moving_from = re.sub(r"^.*?from\s*", "", transfer_details, flags=re.IGNORECASE).strip()
                    elif "to" in transfer_details.lower():
                        moving_from = club_name
                        moving_to = re.sub(r"^.*?to\s*", "", transfer_details, flags=re.IGNORECASE).strip()

                    # Clean any leftover annotations
                    moving_from = re.sub(r",.*$", "", moving_from).strip()
                    moving_to = re.sub(r",.*$", "", moving_to).strip()

                    if player_name and (moving_from != "Unknown" or moving_to != "Unknown"):
                        records.append({
                            "player": player_name,
                            "moving_from": moving_from,
                            "moving_to": moving_to,
                            "fee": transfer_details,
                            "date": "Summer 2026",
                            "register_country": country,
                        })
    return records


def scrape_all_2026_transfers() -> pd.DataFrame:
    """Fetch and parse all 2026 summer transfer pages."""
    all_transfers = []

    for country, url in TRANSFER_URLS.items():
        print(f"\nScraping {country} Summer 2026 Transfers...")
        try:
            req = urllib.request.Request(url, headers=REQ_HEADERS)
            html = urllib.request.urlopen(req, timeout=15).read()
            soup = BeautifulSoup(html, "html.parser")

            if country in ["England", "Italy"]:
                recs = scrape_table_format_a(soup, country)
            else:
                recs = scrape_club_roster_format(soup, country)
                if not recs:  # Fallback to format A
                    recs = scrape_table_format_a(soup, country)

            print(f"  ✓ {country}: extracted {len(recs)} transfers")
            all_transfers.extend(recs)
        except Exception as e:
            print(f"  ⚠ Error scraping {country}: {e}")

    df = pd.DataFrame(all_transfers)
    # Deduplicate
    df = df.drop_duplicates(subset=["player", "moving_from", "moving_to"]).reset_index(drop=True)
    raw_path = DATA_T5_DIR / "transfers_2026_2027_raw.csv"
    df.to_csv(raw_path, index=False)
    print(f"\n✓ Saved total raw 2026 transfers: {raw_path.name} ({len(df):,} transactions)")
    return df


def build_2026_prediction_test_set(transfers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Matches 2026 transfers to master player stats, identifies cross-league moves,
    and structures the benchmark prediction test set.
    """
    print("\n--- Building 2026/2027 Cross-League Prediction Benchmark Test Set ---")
    master_path = DATA_T5_DIR / "big5_player_master_2018_2024.csv"
    if not master_path.exists():
        raise FileNotFoundError(f"Missing master dataset: {master_path}")

    master = pd.read_csv(master_path, low_memory=False)
    team_map = build_team_league_map(master)

    # Determine source and target leagues
    transfers_df["source_league"] = transfers_df["moving_from"].apply(lambda c: match_league(c, team_map))
    transfers_df["target_league"] = transfers_df["moving_to"].apply(lambda c: match_league(c, team_map))

    # Clean player keys for join
    transfers_df["clean_key"] = transfers_df["player"].apply(clean_name)
    master["clean_key"] = master["player"].apply(clean_name)

    # Get latest known season statistics for each player in master
    latest_player_stats = (
        master.sort_values(["season_end_year", "minutes"], ascending=[False, False])
        .drop_duplicates(subset=["clean_key"], keep="first")
    )

    merged = pd.merge(
        transfers_df,
        latest_player_stats,
        on="clean_key",
        how="inner",
        suffixes=("_transfer", "_master"),
    )

    # Cross-league filter: source and target leagues must differ and be known Big 5 leagues
    valid_leagues = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
    
    # If source_league is 'Other' or 'Unknown', fallback to the player's last known league in master
    mask_source_unknown = ~merged["source_league"].isin(valid_leagues)
    merged.loc[mask_source_unknown, "source_league"] = merged.loc[mask_source_unknown, "league"]

    # Now filter for true cross-league transfers between top leagues
    cross_transfers = merged[
        (merged["source_league"].isin(valid_leagues))
        & (merged["target_league"].isin(valid_leagues))
        & (merged["source_league"] != merged["target_league"])
    ].copy()

    # Reorganize columns cleanly
    output_cols = [
        "player_master",
        "clean_key",
        "source_league",
        "target_league",
        "moving_from",
        "moving_to",
        "position",
        "age",
        "minutes",
        "season",
        "goals",
        "assists",
        "xg",
        "xag",
        "goals_p90",
        "assists_p90",
        "xg_p90",
        "xag_p90",
        "shots_p90",
        "shots_on_target_p90",
        "prog_passes_p90",
        "prog_carries_p90",
        "touches_p90",
        "pass_completion_pct",
        "tackles_won_p90",
        "interceptions_p90",
        "fee",
        "date",
    ]
    available_cols = [c for c in output_cols if c in cross_transfers.columns]
    test_set = cross_transfers[available_cols].rename(columns={"player_master": "player"}).drop_duplicates(subset=["player", "source_league", "target_league"])

    test_path = DATA_T5_DIR / "transfers_2026_2027_test_set.csv"
    test_set.to_csv(test_path, index=False)

    print(f"\n  ✓ Successfully built 2026/2027 Prediction Test Set!")
    print(f"  ✓ Saved to: {test_path.name}")
    print(f"  ✓ Total Cross-League 2026/2027 Test Cases: {len(test_set)}")
    print("\n  Sample 2026/2027 Transfer Test Cases:")
    print(test_set[["player", "source_league", "target_league", "moving_from", "moving_to", "goals_p90", "assists_p90"]].head(10).to_string(index=False))

    return test_set


def main():
    print("=" * 70)
    print("2026/2027 SUMMER TRANSFERS INGESTION & TEST SET CREATION")
    print("=" * 70)

    transfers_df = scrape_all_2026_transfers()
    test_set = build_2026_prediction_test_set(transfers_df)

    print("\n" + "=" * 70)
    print("2026/2027 TEST DATASET CREATED SUCCESSFULLY")
    print(f"Location: {DATA_T5_DIR / 'transfers_2026_2027_test_set.csv'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
