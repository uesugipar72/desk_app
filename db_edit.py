import sqlite3

# データベースを作成または接続
db_name = "equipment_management.db"
conn = sqlite3.connect(db_name)

# カーソルを作成
cursor = conn.cursor()

query = """ALTER TABLE room_master ADD COLUMN department_id INTEGER;"""

# クエリを実行
cursor.execute(query)
print("正常に作成されました。")

# コミットして接続を閉じる
conn.commit()
conn.close()
