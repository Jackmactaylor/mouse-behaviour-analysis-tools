import sqlite3
import datetime

conn = sqlite3.connect('/label-studio/data/label_studio.sqlite3')
cursor = conn.cursor()

# Delete existing token for user 1
cursor.execute('DELETE FROM authtoken_token WHERE user_id=1')

# Create new token
new_token = '1234567890123456789012345678901234567890'
created = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

cursor.execute("INSERT INTO authtoken_token (key, created, user_id) VALUES (?, ?, ?)", (new_token, created, 1))

conn.commit()
print(f"Token updated to {new_token}")
conn.close()
