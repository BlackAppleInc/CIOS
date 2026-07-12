import sqlite3
conn = sqlite3.connect('test_cios.db')
with open('infrastructure/database/schema.sql', 'r', encoding='utf-8') as f:
    conn.executescript(f.read())
conn.commit()
conn.close()
print('schema applied')
