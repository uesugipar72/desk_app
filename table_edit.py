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
    equipment_id TEXT UNIQUE NOT NULL,
    categorie TEXT NOT NULL,
    purchase_date TEXT,
    status TEXT CHECK(status IN ('使用中', '良好', '修理中', '廃棄')) DEFAULT '良好',
    borrower TEXT,
    remarks TEXT
);
"""

# クエリを実行
cursor.execute(table_creation_query)
print("器材管理テーブルが正常に作成されました。")

# コミットして接続を閉じる
conn.commit()
conn.close()
