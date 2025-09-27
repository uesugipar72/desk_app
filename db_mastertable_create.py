import sqlite3

# データベースを作成または接続
db_name = "equipment_management.db"
conn = sqlite3.connect(db_name)

# カーソルを作成
cursor = conn.cursor()

# テーブルを作成
tables_name = ["categorie_master","statuse_master","department_master"]
for create_table_name in tables_name:
    print(create_table_name)
    query = f"CREATE TABLE {create_table_name} (ID INT NOT NULL PRIMARY KEY,NAME VARCHAR(255) NOT NULL);"
    # クエリを実行
    cursor.execute(query)
# # カラム名変更　変更したいカラムのマッピング
# rename_columns = {
#     "department": "department_id"
# }
# # ALTER TABLE クエリを順番に実行
# for old_name, new_name in rename_columns.items():
#     query = f"ALTER TABLE equipment RENAME COLUMN {old_name} TO {new_name};"
#     cursor.execute(query)


print("テーブルが正常に作成されました。")

# コミットして接続を閉じる
conn.commit()
conn.close()
