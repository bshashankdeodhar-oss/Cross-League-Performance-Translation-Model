import urllib.request
import pyreadr
import os

tables = [
    "big5_player_shooting",
    "big5_player_passing",
    "big5_player_possession",
    "big5_player_defense"
]

base_url = "https://raw.githubusercontent.com/JaseZiv/worldfootballR_data/mast

er/data/fb_big5_advanced_season_stats/"

for t in tables:
    local_f = f"test_rds/{t}.rds"
    if not os.path.exists(local_f):
        print(f"Downloading {t}...")
        urllib.request.urlretrieve(f"{base_url}{t}.rds", local_f)
    try:
        df = pyreadr.read_r(local_f)[None]
        print(f"✓ {t}: Shape {df.shape}")
        print(f"   Cols: {df.columns.tolist()[:10]}")
    except Exception as e:
        print(f"✗ Error reading {t}: {e}")
