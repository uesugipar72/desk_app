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

def display_repair_history(equipment_id):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT status, request_date, completion_date, category, vendor, technician
        FROM repair
        WHERE equipment_id = ?
        ORDER BY request_date DESC;
    """, (equipment_id,))
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
def open_edit_repair():
    try:
        children = repair_frame.winfo_children()
        tree = None
        for child in children:
            if isinstance(child, ttk.Treeview):
                tree = child
                break

        if tree is None:
            messagebox.showerror("エラー", "修理履歴が見つかりません。")
            return

        selected = tree.selection()
        if not selected:
            messagebox.showwarning("選択なし", "修正する修理情報を選択してください。")
            return

        selected_data = tree.item(selected[0], "values")
        print("選択された修理データ:", selected_data)

        EditRepairWindow(root_edit, db_name, equipment_data["equipment_id"], selected_data, categories, cellers)
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
keys = ["categorie_name", "equipment_id", "name", "statuse_name", "department_name", "room_name", "manufacturer_name", "celler_name", "remarks", "purchase_date", "model"]

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

# --- 修理履歴表示 ---
if equipment_data.get("equipment_id"):
    display_repair_history(equipment_data["equipment_id"])

root_edit.mainloop()
