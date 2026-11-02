import sqlite3

conn = sqlite3.connect("transferpred.db")
c = conn.cursor()
c.execute("SELECT t.team_name, l.league_name FROM Team t JOIN League l ON t.league_id = l.league_id WHERE t.team_name IN ('Pisa', 'Paris FC')")
print(c.fetchall())
