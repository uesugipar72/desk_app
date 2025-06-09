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
from cls_edit_repair_window import EditRepairWindow  # 追加
# データベース接続設定
db_name = "equipment_management.db"
fetcher = MasterDataFetcher(db_name)  # MasterDataFetcherをインスタンス化

equipment_data = {}  # ← グローバルスコープで宣言しておく
# 各マスタテーブルからデータ取得
categorys = fetcher.fetch_all("category_master")
statuses = fetcher.fetch_all("status_master")
departments = fetcher.fetch_all("department_master")
rooms = fetcher.fetch_all("room_master")
manufacturers = fetcher.fetch_all("manufacturer_master")
cellers = fetcher.fetch_all("celler_master")
repaircategories = fetcher.fetch_all("repair_category_master")
repairstatuses = fetcher.fetch_all("repair_status_master")
# デフォルト値を設定（万が一データがない場合）
if not repaircategories:
    repaircategories = [(1, "随意対応"), (2, "保守対応"), (3, "対応未定"), (4, "修理不能"), (5, "使用不能")]
if not repairstatuses:
    repairstatuses = [(1, "修理依頼中"), (2, "修理不能"), (3, "修理完了"), (4, "更新申請中"), (5, "廃棄")]
if not departments:
    departments = [(1, "検査科"), (2, "検体検査"), (3, "生理検査"), (4, "細菌検査"), (5, "病理検査"), (6, "採血室")]

def fetch_equipment_detail(equipment_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM equipment WHERE equipment_id = ?", (equipment_id,))
    result = cursor.fetchone()
    conn.close()
    return result
    # equipment_data = {}

def get_id_from_name(name, data_list):
    """名称に対応するIDを取得する"""
    for item_id, item_name in data_list:
        if item_name == name:
            return item_id
    return None  # 該当なしの場合はNone

def display_repair_history(equipment_id):
    global repair_tree

    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            rs.name AS repairstatus_name,
            r.request_date,
            r.completion_date,
            rc.name AS repaircategory_name,
            c.name AS vendor_name,
            r.technician
        FROM repair r
        LEFT JOIN repair_status_master rs ON r.repairstatuses = rs.id
        LEFT JOIN repair_category_master rc ON r.repaircategories = rc.id
        LEFT JOIN celler_master c ON r.cellers = c.id
        WHERE r.equipment_id = ?
        ORDER BY r.request_date DESC;
    """, (equipment_id,))
    repairs = cursor.fetchall()
    conn.close()

    # 表示列設定
    columns = ["状態", "依頼日", "完了日", "カテゴリ", "業者", "技術者"]

    if 'repair_tree' not in globals():
        repair_tree = ttk.Treeview(repair_frame, columns=columns, show='headings', height=20)
        for col in columns:
            repair_tree.heading(col, text=col)
            repair_tree.column(col, width=100, anchor='center')
        repair_tree.pack(fill=tk.BOTH, expand=True)
    else:
        # 既存の内容をクリア
        for item in repair_tree.get_children():
            repair_tree.delete(item)

    # データを挿入
    for row in repairs:
        repair_tree.insert('', tk.END, values=row)

def open_edit_repair():
    try:
        if 'repair_tree' not in globals():
            messagebox.showerror("エラー", "修理履歴が見つかりません。")
            return

        selected = repair_tree.selection()
        if not selected:
            messagebox.showwarning("選択なし", "修正する修理情報を選択してください。")
            return

        selected_data = repair_tree.item(selected[0], "values")
        print("選択された修理データ:", selected_data)

        # コールバック関数を渡す
        EditRepairWindow(
            parent=root_edit,
            db_name=db_name,
            equipment_id=equipment_data["equipment_id"],
            selected_data=selected_data,
            categories=repaircategories,
            vendors=cellers,
            refresh_callback=lambda: display_repair_history(equipment_data["equipment_id"])  # ← 追加
        )
    except Exception as e:
        messagebox.showerror("例外発生", f"エラーが発生しました:\n{e}")

# キャンセル関数
def cancel_edit():
    root_edit.destroy()

# メインウィンドウ
root_edit = tk.Tk()
root_edit.title("器材情報（参照）")

# メインウィンドウレイアウト調整
main_frame = tk.Frame(root_edit)
main_frame.pack(fill=tk.BOTH, expand=True)

form_frame = tk.Frame(main_frame)
form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

repair_frame = tk.Frame(main_frame)
repair_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

input_vars = {}
labels = ["カテゴリ名", "器材番号", "器材名", "状態", "部門", "部屋", "製造元", "販売元", "備考", "購入日", "モデル(シリアル)"]
keys = ["category_name", "equipment_id", "name", "statuse_name", "department_name", "room_name", "manufacturer_name", "celler_name", "remarks", "purchase_date", "model"]

for i, (label, key) in enumerate(zip(labels, keys)):
    tk.Label(form_frame, text=label).grid(row=i, column=0, padx=5, pady=3)
    var = tk.StringVar(value=equipment_data.get(key, ""))
    input_vars[key] = var

    entry = tk.Entry(form_frame, textvariable=var, state="readonly")
    entry.grid(row=i, column=1, padx=5, pady=3)

# --- ボタンエリア ---
button_frame = tk.Frame(form_frame)
button_frame.grid(row=len(labels), column=0, columnspan=2, pady=20)

def open_add_repair():
    messagebox.showinfo("修理情報追加", "修理情報追加画面を開く処理をここに記述してください。")


btn_add_repair = tk.Button(button_frame, text="修理情報追加", command=open_add_repair)
btn_add_repair.pack(side=tk.LEFT, padx=5)

btn_edit_repair = tk.Button(button_frame, text="修理情報修正", command=open_edit_repair)
btn_edit_repair.pack(side=tk.LEFT, padx=5)

btn_cancel = tk.Button(button_frame, text="戻る", command=root_edit.destroy)
btn_cancel.pack(side=tk.LEFT, padx=5)

def launch_repair_info(equipment_id):
    global equipment_data

    data = fetch_equipment_detail(equipment_id)
    if data:
        equipment_data = {
            "equipment_id": data[1],
            "category_name": fetcher.fetch_name_by_id("category_master", data[4]),
            "name": data[2],
            "statuse_name": fetcher.fetch_name_by_id("status_master", data[5]),
            "department_name": fetcher.fetch_name_by_id("department_master", data[6]),
            "room_name": fetcher.fetch_name_by_id("room_master", data[7]),
            "manufacturer_name": fetcher.fetch_name_by_id("manufacturer_master", data[8]),
            "celler_name": fetcher.fetch_name_by_id("celler_master", data[9]),
            "purchase_date": data[11],
            "model": data[12],
            "remarks": data[10],
        }

        for key, var in input_vars.items():
            var.set(equipment_data.get(key, ""))

        display_repair_history(equipment_id)
        root_edit.mainloop()
    else:
        messagebox.showerror("データエラー", f"equipment_id = {equipment_id} のデータが見つかりません。")

# --- 修理履歴表示 ---
# if equipment_data.get("equipment_id"):
    # display_repair_history(equipment_data["equipment_id"])

if __name__ == "__main__":
    # サンプル用equipment_id（適宜、実際に存在するIDに差し替えてください）
    equipment_id = "0001"
    if len(sys.argv) > 1:
        equipment_id = sys.argv[1]
        launch_repair_info(equipment_id)
    else:
        messagebox.showerror("引数エラー", "器材IDが指定されていません。")
        print("器材IDが指定されていません。例: python repair_info.py {equipment_id}")
        sys.exit(1)