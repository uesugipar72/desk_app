import sqlite3
import json
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from cls_master_data_fetcher import MasterDataFetcher
from cls_new_equipment_number import EquipmentManager

# データベース接続設定
db_name = "equipment_management.db"
fetcher = MasterDataFetcher(db_name)
manager = EquipmentManager()  # 新しいequipment番号を生成

# 各マスタテーブルからデータ取得
categories = fetcher.fetch_all("categorie_master")
statuses = fetcher.fetch_all("statuse_master")
departments = fetcher.fetch_all("department_master")
rooms = fetcher.fetch_all("room_master")
manufacturers = fetcher.fetch_all("manufacturer_master")
cellers = fetcher.fetch_all("celler_master")

def get_id_from_name(name, data_list):
    """選択した名前に対応するIDを取得"""
    for item_id, item_name in data_list:
        if item_name == name:
            return item_id
    return None

def add_equipment():
    """新規器材をデータベースに登録"""
    new_data = {key: var.get() for key, var in input_vars.items()}
    new_data["equipment_code"] = equipment_code  # 事前に取得したIDを使用

    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # 各IDを取得
        categorie_id = get_id_from_name(new_data["categorie_name"], categories)
        statuse_id = get_id_from_name(new_data["statuse_name"], statuses)
        department_id = get_id_from_name(new_data["department_name"], departments)
        manufacturer_id = get_id_from_name(new_data["manufacturer_name"], manufacturers)
        room_id = get_id_from_name(new_data["room_name"], rooms)
        celler_id = get_id_from_name(new_data["celler_name"], cellers)

        query = """
        INSERT INTO equipment (equipment_code, categorie_id, name, statuse_id, department_id, room_id, manufacturer_id, celler_id, purchase_date, remarks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        cursor.execute(query, (
            new_data["equipment_code"],
            categorie_id,
            new_data["name"],
            statuse_id,
            department_id,
            room_id,
            manufacturer_id,
            celler_id,
            new_data["purchase_date"],
            new_data["remarks"]
        ))
        conn.commit()
        messagebox.showinfo("成功", "新しい器材が追加されました。")
    except sqlite3.Error as e:
        messagebox.showerror("データベースエラー", str(e))
    finally:
        conn.close()
        root_add.destroy()

# ** GUI作成 **
root_add = tk.Tk()
root_add.title("新規器材登録")
root_add.geometry("400x550")

# ** 事前に新しい equipment_code を取得 **
equipment_code = manager.get_next_equipment_code()

# ** equipment_code の表示 **
tk.Label(root_add, text="器材番号").grid(row=0, column=0, padx=10, pady=5)
tk.Label(root_add, text=equipment_code, fg="blue", font=("Arial", 12, "bold")).grid(row=0, column=1, padx=10, pady=5)

# ** 各種入力フィールド **
input_vars = {}
labels = ["カテゴリ名", "器材名", "状態", "部門", "部屋", "製造元", "販売元", "購入日", "備考"]
keys = ["categorie_name", "name", "statuse_name", "department_name", "room_name", "manufacturer_name", "celler_name", "purchase_date", "remarks"]

for i, (label, key) in enumerate(zip(labels, keys)):
    tk.Label(root_add, text=label).grid(row=i+1, column=0, padx=10, pady=5)
    var = tk.StringVar()
    input_vars[key] = var
    
    if key in ["categorie_name", "statuse_name", "department_name", "room_name", "manufacturer_name", "celler_name"]:
        key_prefix = key.split("_", 1)[0]
        combo_values = [name for _, name in locals().get(key_prefix + 's', [])]
        entry = ttk.Combobox(root_add, textvariable=var, values=combo_values, state="readonly")
    elif key == "purchase_date":
        entry = DateEntry(root_add, textvariable=var, date_pattern='yyyy-MM-dd')
    else:
        entry = tk.Entry(root_add, textvariable=var)
    entry.grid(row=i+1, column=1, padx=10, pady=5)

# ** ボタン **
tk.Button(root_add, text="保存", command=add_equipment).grid(row=len(labels)+1, column=0, pady=20)
tk.Button(root_add, text="キャンセル", command=root_add.destroy).grid(row=len(labels)+1, column=1, pady=20)

root_add.mainloop()
