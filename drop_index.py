import sqlite3
conn = sqlite3.connect('test_cios.db')
conn.execute("DROP INDEX IF EXISTS idx_opportunity_cases_status_updated")
conn.commit()
conn.close()
print('dropped')
