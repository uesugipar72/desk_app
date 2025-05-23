# import subprocess
# import os
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
db_name = "equipment_management.db"
fetcher = MasterDataFetcher(db_name)  # MasterDataFetcherをインスタンス化

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

# データ挿入関数
def save_equipment():
    updated_data = {}
    for key, var in input_vars.items():
        if equipment_data.get(key, "") != var.get():
            updated_data[key] = var.get()
    
    if updated_data:
        try:
            conn = sqlite3.connect(db_name)
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
            WHERE equipment_id = ?;
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
                equipment_data["equipment_id"]
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

window_width = 400
window_height = 500
screen_width = root_edit.winfo_screenwidth()
screen_height = root_edit.winfo_screenheight()
position_top = int(screen_height / 2 - window_height / 2)
position_right = int(screen_width / 2 - window_width / 2)
root_edit.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")

input_vars = {}
labels = ["カテゴリ名", "器材番号", "器材名", "状態", "部門", "部屋", "製造元","販売元", "備考","購入日", "モデル(シリアル)"]
keys = ["categorie_name", "equipment_id", "name", "statuse_name", "department_name", "room_name", "manufacturer_name", "celler_name", "remarks", "purchase_date", "model"]

for i, (label, key) in enumerate(zip(labels, keys)):
    tk.Label(root_edit, text=label).grid(row=i, column=0, padx=10, pady=5)
    var = tk.StringVar(value=equipment_data.get(key, ""))
    input_vars[key] = var
    
    if key in ["categorie_name", "statuse_name", "department_name", "room_name", "manufacturer_name", "celler_name"]:
        # コンボボックスの作成
        key_prefix = key.split("_", 1)[0]  # アンダースコア前の文字列を取得
        combo_values = [name for _, name in locals().get(key_prefix + 's', [])]
        entry = ttk.Combobox(root_edit, textvariable=var, values=combo_values, state="readonly")
    elif key == "purchase_date":
        entry = DateEntry(root_edit, textvariable=var, date_pattern='yyyy-MM-dd')
    else:
        entry = tk.Entry(root_edit, textvariable=var)
    entry.grid(row=i, column=1, padx=10, pady=5)

save_button = tk.Button(root_edit, text="保存", command=save_equipment)
save_button.grid(row=len(labels), column=0, pady=20)

cancel_button = tk.Button(root_edit, text="キャンセル", command=cancel_edit)
cancel_button.grid(row=len(labels), column=1, pady=20)

root_edit.mainloop()
