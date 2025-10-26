import sqlite3

# データベースを作成または接続
db_name = "equipment_management.db"
conn = sqlite3.connect(db_name)

# カーソルを作成
cursor = conn.cursor()

# テーブルを作成
# table_creation_query = """
# CREATE TABLE IF NOT EXISTS equipment (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     equipment_code TEXT UNIQUE NOT NULL,
#     categorie TEXT NOT NULL,
#     purchase_date TEXT,
#     status TEXT CHECK(status IN ('使用中', '良好', '修理中', '廃棄')) DEFAULT '良好',
#     borrower TEXT,
#     remarks TEXT
# );
# """
table_creation_query = """
CREATE TABLE IF NOT EXISTS repair (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_code INTEGER NOT NULL,
    status TEXT CHECK(status IN ('依頼中', '修理中', '完了', 'キャンセル')) DEFAULT '依頼中',
    request_date TEXT,
    completion_date TEXT,
    category TEXT,
    details TEXT,
    vendor TEXT,
    technician TEXT,
    cost REAL,
    remarks TEXT,
    FOREIGN KEY (equipment_code) REFERENCES equipment(id) ON DELETE CASCADE
);
"""

# クエリを実行
cursor.execute(table_creation_query)
print("器材管理テーブルが正常に作成されました。")

# コミットして接続を閉じる
conn.commit()
conn.close()
