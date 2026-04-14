import sqlite3, os
db = "intellicredit.db"
if not os.path.exists(db):
    print("DB missing")
else:
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("Tables:", [r[0] for r in cur.fetchall()])
    cur.execute("SELECT id, status FROM applications ORDER BY created_at DESC LIMIT 3")
    print("Apps:", cur.fetchall())
    cur.execute("SELECT agent_name, status, output_summary FROM agent_logs ORDER BY logged_at DESC LIMIT 10")
    print("Logs:", cur.fetchall())
    conn.close()
