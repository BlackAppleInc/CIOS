import sqlite3
conn = sqlite3.connect('test_cios.db')
cur = conn.cursor()
queries = [
    ("EXPLAIN QUERY PLAN SELECT oc.id, oc.status FROM opportunity_cases oc WHERE oc.status NOT IN ('Closed','Offer')", ()),
    ("EXPLAIN QUERY PLAN SELECT * FROM interactions WHERE opportunity_id = ? ORDER BY interaction_date DESC", (1,)),
    ("EXPLAIN QUERY PLAN SELECT * FROM application_events WHERE opportunity_id = ?", (1,)),
    ("EXPLAIN QUERY PLAN SELECT DISTINCT opportunity_id FROM interactions WHERE contact_id = ?", (1,)),
]
for q, params in queries:
    print(q)
    for row in cur.execute(q, params).fetchall():
        print(' ', row)
    print()
