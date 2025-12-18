import sqlite3

try:
    conn = sqlite3.connect('label-studio_data/label_studio.sqlite3')
    cursor = conn.cursor()
    
    print("--- Tokens ---")
    cursor.execute("SELECT * FROM authtoken_token")
    tokens = cursor.fetchall()
    for t in tokens:
        print(t)
        
    print("\n--- Users ---")
    # Try htx_user or auth_user
    try:
        cursor.execute("SELECT id, email FROM htx_user")
        users = cursor.fetchall()
        for u in users:
            print(u)
    except:
        print("htx_user not found or error")

except Exception as e:
    print(e)
finally:
    if conn:
        conn.close()
