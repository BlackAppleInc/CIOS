import sqlite3
conn = sqlite3.connect('test_cios.db')
cur = conn.cursor()
for row in cur.execute("PRAGMA index_list('opportunity_cases')").fetchall():
    print(row)
