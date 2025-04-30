import pandas as pd
import sqlite3

# CSVをUTF-8で読み込む（先頭行をカラム名にする）
df = pd.read_csv("list2_utf8_fixed.csv")

# SQLiteデータベースに接続
conn = sqlite3.connect("equipment_management.db")

# データフレームをSQLへ書き込み（テーブル名は適宜変更）
df.to_sql("my_table", conn, if_exists="replace", index=False)

# 接続を閉じる
conn.close()
