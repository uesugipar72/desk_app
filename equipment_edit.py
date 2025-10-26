# import subprocess
import os
import sys
import json
from tkinter import ttk
import tkinter as tk
from tkinter import messagebox
from tkcalendar import DateEntry
from cls_master_data_fetcher import MasterDataFetcher
import sqlite3
from cls_new_equipment_number import EquipmentManager

# データベース接続設定
# JSON設定ファイルを読み込む
config_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

DB_NAME = config.get("db_name", "equipment_management.db")  # デフォルトあり
#db_name = "equipment_management.db"
fetcher = MasterDataFetcher(DB_NAME)  # MasterDataFetcherをインスタンス化

# 各マスタテーブルからデータ取得
categories = fetcher.fetch_all("categorie_master")
statuses = fetcher.fetch_all("statuse_master")
departments = fetcher.fetch_all("department_master")
rooms = fetcher.fetch_all("room_master")
manufacturers = fetcher.fetch_all("manufacturer_master")
cellers = fetcher.fetch_all("celler_master")

# デフォルト値を設定（万が一データがない場合）
if not categories:
    categories = [(1, "検査機器"), (2, "一般備品"), (3, "消耗品"), (4, "その他")]
if not statuses:
    statuses = [(1, "使用中"), (2, "良好"), (3, "修理中"), (4, "廃棄")]
if not departments:
    departments = [(1, "検査科"), (2, "検体検査"), (3, "生理検査"), (4, "細菌検査"), (5, "病理検査"), (6, "採血室")]

# コマンドライン引数からデータを取得
if len(sys.argv) > 1:
    try:
        equipment_data = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        messagebox.showerror("エラー", "データの読み込みに失敗しました。")
        sys.exit(1)
else:
    equipment_data = {}

def get_id_from_name(name, data_list):
    """名称に対応するIDを取得する"""
    for item_id, item_name in data_list:
        if item_name == name:
            return item_id
    return None  # 該当なしの場合はNone

def display_repair_history(equipment_code):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status, request_date, completion_date, category, vendor, technician
        FROM repair
        WHERE equipment_code = ?
        ORDER BY request_date DESC;
    """, (equipment_code,))
    repairs = cursor.fetchall()
    conn.close()

    # Treeview の列設定
    columns = ["status", "request_date", "completion_date", "category", "vendor", "technician"]
    tree = ttk.Treeview(repair_frame, columns=columns, show='headings', height=20)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100, anchor='center')
    tree.pack(fill=tk.BOTH, expand=True)

    for row in repairs:
        tree.insert('', tk.END, values=row)


# データ挿入関数
def save_equipment():
    updated_data = {}
    for key, var in input_vars.items():
        if equipment_data.get(key, "") != var.get():
            updated_data[key] = var.get()
    
    if updated_data:
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # 各名称に対応するIDを取得
            categorie_id = get_id_from_name(updated_data.get("categorie_name", equipment_data["categorie_name"]), categories)
            statuse_id = get_id_from_name(updated_data.get("statuse_name", equipment_data["statuse_name"]), statuses)
            department_id = get_id_from_name(updated_data.get("department_name", equipment_data["department_name"]), departments)
            manufacturer_id = get_id_from_name(updated_data.get("manufacturer_name", equipment_data["manufacturer_name"]), manufacturers)
            room_id = get_id_from_name(updated_data.get("room_name", equipment_data["room_name"]), rooms)
            celler_id = get_id_from_name(updated_data.get("celler_name", equipment_data["celler_name"]), cellers)

            query = """
            UPDATE equipment
            SET categorie_id = ?, name = ?, statuse_id = ?, department_id = ?, room_id = ?, manufacturer_id=?, celler_id = ?, purchase_date = ?, remarks = ?, model = ?
            WHERE equipment_code = ?;
            """
            cursor.execute(query, (
                categorie_id,
                updated_data.get("name", equipment_data["name"]),
                statuse_id,
                department_id,
                room_id,
                manufacturer_id,
                celler_id,
                updated_data.get("purchase_date", equipment_data["purchase_date"]),
                updated_data.get("remarks", equipment_data["remarks"]),
                updated_data.get("model", equipment_data["model"]),
                equipment_data["equipment_code"]
            ))

            conn.commit()
        except sqlite3.Error as e:
            print("データベースエラー:", e)
        else:
            messagebox.showinfo("成功", "データが更新されました。")
        finally:
            conn.close()
                   
    root_edit.destroy()

# キャンセル関数
def cancel_edit():
    root_edit.destroy()

# メインウィンドウ
root_edit = tk.Tk()
root_edit.title("器材情報修正")

# メインウィンドウレイアウト調整
main_frame = tk.Frame(root_edit)
main_frame.pack(fill=tk.BOTH, expand=True)

form_frame = tk.Frame(main_frame)
form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

repair_frame = tk.Frame(main_frame)
repair_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

input_vars = {}
labels = ["カテゴリ名", "器材番号", "器材名", "状態", "部門", "部屋", "製造元","販売元", "備考","購入日", "モデル(シリアル)"]
keys = ["categorie_name", "equipment_code", "name", "statuse_name", "department_name", "room_name", "manufacturer_name", "celler_name", "remarks", "purchase_date", "model"]

for i, (label, key) in enumerate(zip(labels, keys)):
    tk.Label(form_frame, text=label).grid(row=i, column=0, padx=5, pady=3)
    var = tk.StringVar(value=equipment_data.get(key, ""))
    input_vars[key] = var
    
    if key in ["categorie_name", "statuse_name", "department_name", "room_name", "manufacturer_name", "celler_name"]:
        # コンボボックスの作成
        key_prefix = key.split("_", 1)[0]  # アンダースコア前の文字列を取得
        combo_values = [name for _, name in locals().get(key_prefix + 's', [])]
        entry = ttk.Combobox(form_frame, textvariable=var, values=combo_values, state="readonly")
    elif key == "purchase_date":
        entry = DateEntry(form_frame, textvariable=var, date_pattern='yyyy-MM-dd')
    else:
        entry = tk.Entry(form_frame, textvariable=var)
        entry.grid(row=i, column=1, padx=5, pady=3)

save_button = tk.Button(form_frame, text="保存", command=save_equipment)
save_button.grid(row=len(labels), column=0, pady=20)

cancel_button = tk.Button(form_frame, text="戻る", command=cancel_edit)
cancel_button.grid(row=len(labels), column=1, pady=20)

if equipment_data.get("equipment_code"):
    display_repair_history(equipment_data["equipment_code"])

root_edit.mainloop()
