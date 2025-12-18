import sqlite3

try:
    conn = sqlite3.connect('label-studio_data/label_studio.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    # Check for authtoken_token
    if ('authtoken_token',) in tables:
        cursor.execute("SELECT * FROM authtoken_token")
        print("Tokens:", cursor.fetchall())
        
    # Check for users to map user_id
    if ('auth_user',) in tables:
        cursor.execute("SELECT id, email FROM auth_user")
        print("Users:", cursor.fetchall())

except Exception as e:
    print(e)
finally:
    if conn:
        conn.close()
