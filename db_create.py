import sqlite3

# データベースを作成または接続
db_name = "equipment_management.db"
conn = sqlite3.connect(db_name)

# カーソルを作成
cursor = conn.cursor()

# テーブルを作成
table_creation_query = """
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    equipment_code INTEGER UNIQUE NOT NULL,
    categorie_id INTEGER NOT NULL,
    purchase_date TEXT NOT NULL,
    status_id INTEGER NOT NULL,
    borrower TEXT,
    remarks TEXT
);
"""

# # カラム名変更　変更したいカラムのマッピング
# rename_columns = {
#     "department": "department_id"
# }
# # ALTER TABLE クエリを順番に実行
# for old_name, new_name in rename_columns.items():
#     query = f"ALTER TABLE equipment RENAME COLUMN {old_name} TO {new_name};"
#     cursor.execute(query)

# クエリを実行
cursor.execute(table_creation_query)
print("器材管理テーブルが正常に作成されました。")

# コミットして接続を閉じる
conn.commit()
conn.close()
