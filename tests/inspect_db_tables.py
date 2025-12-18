import sqlite3
import os

db_path = 'label-studio_data/label_studio.sqlite3'

if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables found:")
        for t in tables:
            print(f"- {t[0]}")
            
        # Check columns in authtoken_token
        print("\nColumns in authtoken_token:")
        cursor.execute("PRAGMA table_info(authtoken_token)")
        columns = cursor.fetchall()
        for c in columns:
            print(c)
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
