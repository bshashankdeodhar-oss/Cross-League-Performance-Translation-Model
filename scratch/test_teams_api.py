import urllib.request
import urllib.parse
import json

data = urllib.parse.urlencode({'username': 'viewer', 'password': 'viewer123'}).encode()
req = urllib.request.Request('http://127.0.0.1:8000/auth/login', data=data)
with urllib.request.urlopen(req) as resp:
    token = json.loads(resp.read().decode())['access_token']

headers = {'Authorization': f'Bearer {token}'}
for lg in ['Premier League', 'Bundesliga', 'La Liga', 'Serie A', 'Ligue 1']:
    encoded_lg = urllib.parse.quote(lg)
    req = urllib.request.Request(f'http://127.0.0.1:8000/teams?league={encoded_lg}', headers=headers)
    with urllib.request.urlopen(req) as resp:
        teams = json.loads(resp.read().decode())
        t_names = [t['team'] for t in teams]
        print(f"{lg}: {len(teams)} teams.")
        print(f"  Sample: {t_names[:6]}")
        # Check specific new/promoted teams
        for check in ['Como', 'Ipswich Town', 'St. Pauli', 'Holstein Kiel', 'Leganés', 'Auxerre', 'Angers', 'Sunderland', 'Oviedo', 'Pisa', 'Paris FC']:
            if check in t_names:
                print(f"    [OK] {check} present")
