import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont 
from equipment_sarch import fetch_data
from cls_master_data_fetcher import MasterDataFetcher
import subprocess
import json
from open_master_list import open_master_list_window
from tkinter import messagebox
import sqlite3
import json


db_name = "equipment_management.db"
fetcher = MasterDataFetcher(db_name)  # MasterDataFetcherをインスタンス化

# 各マスタテーブルからデータ取得
categories = fetcher.fetch_all("categorie_master")
statuses = fetcher.fetch_all("statuse_master")
departments = fetcher.fetch_all("department_master")
cellers = fetcher.fetch_all("celler_master")
manufacturers = fetcher.fetch_all("manufacturer_master")
rooms = fetcher.fetch_all("room_master")
# デフォルト値を設定（万が一データがない場合）
if not categories:
    categories = [(1, "検査機器"), (2, "一般備品"), (3, "消耗品"), (4, "その他")]
if not statuses:
    statuses = [(1, "使用中"), (2, "良好"), (3, "修理中"), (4, "廃棄")]
if not departments:
    departments = [(1, "検査科"), (2, "検体検査"), (3, "生理検査"), (4, "細菌検査"), (5, "病理検査"), (6, "採血室")]
if not rooms:
    rooms = [(1, "受付_染色室"), (2, "鏡検室"), (3, "臓器固定・切出室"), (4, "標本作製室"),(5, "病理標本保人室"),(6, "病理診断室"),(8, "剖検室"),(9, "剖検前室")]

def populate_master_menu():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [table[0] for table in cursor.fetchall()]
    conn.close()
    return tables

def search():
    # 選択されたカテゴリー名を取得
    categorie_name = combo_categorie.get()
    # カテゴリー名に対応する categorie_id を取得
    categorie_id = None
    for cat in categories:
        if cat[1] == categorie_name:
            categorie_id = cat[0]  # IDを取得
            break
   
    statuse_name = entries["機器状況"].get() 
    statuse_id = None
    for stat in statuses:
        if stat[1] == statuse_name:
            statuse_id = stat[0]  # IDを取得
            break    

    department_name = entries["部門"].get()
    department_id = None
    for depa in departments:
        if depa[1] == department_name:
            department_id = depa[0]  # IDを取得
            break

    room_name = entries["部屋"].get()
    room_id = room_name
    for room in rooms:
        if room[1] == room_name:
            room_id = room[0]  # IDを取得
            break
    manufacturer_name = entries["製造元"].get()
    manufacturer_id = None
    for manu in manufacturers:
        if manu[1] == manufacturer_name:
            manufacturer_id = manu[0]
            break

    celler_name = entries["販売元"].get()
    celler_id = None
    for cell in cellers:
        if cell[1] == celler_name:
            celler_id = cell[0]
            break

    # 他の検索条件の取得
    equipment_code = entries["機器コード"].get() if entries["機器コード"].get() else None
    name = entries["機器名"].get() if entries["機器名"].get() else None
    name_kana = entries["機器名カナ"].get() if entries["機器名カナ"].get() else None
    remarks = entries["備考"].get() if entries["備考"].get() else None
    manufacturer = entries["製造元"].get() if entries["製造元"].get() else None

    print(f"機器コード: {equipment_code}")
    print(f"機器名: {name}")
    print(f"機器名カナ: {name_kana}")
    print(f"分類ID: {categorie_id}")
    print(f"状態ID: {statuse_id}")
    print(f"部門ID: {department_id}")
    print(f"機器状況ID: {department_id}")
    print(f"部屋ID: {room_id}")
    print(f"備考: {remarks}")
    print(f"製造元ID: {manufacturer_id}")
    print(f"販売元ID: {celler_id}")
    # データ取得
    
    records = fetch_data(equipment_code, name, name_kana, categorie_id, statuse_id, department_id, room_id , manufacturer_id, celler_id, remarks)
    # print(f"レコード内容; {records}")
    # 既存のデータをクリア
    for row in tree.get_children():
        tree.delete(row)

     # 新しいデータを挿入
    for index, record in enumerate(records):
        # IDに一致する文字情報に変換
        categorie_name = next((name for id, name in categories if id == record[4]), "不明")        
        statuse_name = next((name for id, name in statuses if id == record[5]), "不明")
        department_name = next((name for id, name in departments if id == record[6]), "不明")
        room_name = next((name for id, name in rooms if id == record[7]), "不明")
        manufacturer_name = next((name for id, name in manufacturers if id == record[8]), "不明")
        celler_name = next((name for id, name in cellers if id == record[9]), "不明")
        
        # 偶数行・奇数行でタグを分ける
        tag = "evenrow" if index % 2 == 0 else "oddrow"

        tree.insert("", tk.END, values=(
            categorie_name, record[1], record[2], statuse_name, department_name, 
            room_name, manufacturer_name, celler_name, record[10], record[11], record[12]
        ), tags=(tag,))
        set_fixed_column_widths(tree)

    # ★ カラム幅自動調整機能の追加（文字幅に応じて）

def create_equipment_treeview(parent): 
    """
    機器データを表示する Treeview を作成（カラム・タグ付き）
    """
    columns = (
        "機器分類", "機器コード", "機器名", "状態", "部門", "部屋",
        "製造元", "販売元", "備考", "購入日", "モデル"
    )

    tree = ttk.Treeview(parent, columns=columns, show="headings")

    # カラム設定
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150, anchor="w")

    # 行の背景色用タグ設定
    tree.tag_configure("evenrow", background="#F0F0FF")  # 薄い青グレー
    tree.tag_configure("oddrow", background="#FFFFFF")   # 白

    tree.pack(fill=tk.BOTH, expand=True)
    return tree
def set_fixed_column_widths(treeview, json_path="column_widths.json"):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            widths = json.load(f)
    except FileNotFoundError:
        print("カラム幅ファイルが見つかりません。デフォルト幅で表示されます。")
        return

    for col in treeview["columns"]:
        if col in widths:
            treeview.column(col, width=widths[col])



def on_tree_item_double_click(event):
    selected_item = tree.selection()
    if selected_item:
        values = tree.item(selected_item[0], "values")
        equipment_data = {
            "categorie_name": values[0],
            "equipment_code": values[1],
            "name": values[2],
            "statuse_name": values[3],
            "department_name": values[4],
            "room_name":values[5],
            "manufacturer_name": values[6],
            "celler_name": values[7],
            "remarks": values[8],
            "purchase_date": values[9],
            "model": values[10],
        }

        # JSON文字列に変換
        equipment_json = json.dumps(equipment_data)

        # subprocessの実行（適切に引数を渡す）
        subprocess.run(["python", "equipment_edit.py", equipment_json])
        root.focus_force()
        search()


def reset_conditions():
    print("条件初期化ボタンが押されました")
    combo_categorie.set("")  # コンボボックスの選択をクリア
    for key, entry in entries.items():
        if isinstance(entry, ttk.Combobox):  
            entry.set("")  # コンボボックスをクリア
        else:
            entry.delete(0, tk.END)  # テキストエントリーをクリア


# メインウィンドウの作成
root = tk.Tk()
root.title("器材管理システム")
root.geometry("1400x750")

menubar = tk.Menu(root)
master_menu = tk.Menu(menubar, tearoff=0)

table_list = populate_master_menu()
for table_name in table_list:
     master_menu.add_command(
        label=table_name,
        command=lambda t=table_name: open_master_list_window(root, t)
    )

menubar.add_cascade(label="マスタデータ", menu=master_menu)
root.config(menu=menubar)
root.option_add("*Font", ("MS UI Gothic", 11))


# フレームの作成
frame_top = ttk.Frame(root)
frame_top.pack(fill=tk.X, padx=10, pady=5)

frame_search = ttk.Frame(root)
frame_search.pack(fill=tk.X, padx=10, pady=5)

frame_table = ttk.Frame(root)
frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)


# 施設情報
lbl_facility = ttk.Label(frame_top, text="施設:")
lbl_facility.grid(row=0, column=0, padx=5, pady=5)
entry_facility = ttk.Entry(frame_top)
entry_facility.grid(row=0, column=1, padx=5, pady=5)
entry_facility.insert(0, "0000000001 複十字病院　病理診断科")

# 検索条件ラベルとエントリーフィールドの作成
labels = [
    "機器分類", "機器コード", "機器名", "機器名カナ", "機器状況", "部門","部屋" ,"備考", "製造元",
    "販売元", "販売担当者", "連絡先", "購入日", "予備１", "予備２",
    "予備３", "予備４", "予備５", "予備６", "予備７", "予備８",
    "予備９", "予備１０", "予備１１", "予備１２", "予備１３"
]

entries = {}
for i, label in enumerate(labels):
    lbl = ttk.Label(frame_search, text=label)
    lbl.grid(row=i//4, column=(i%4)*2, padx=5, pady=5)
    
    # コンボボックスを使用する項目
    if label == "機器分類":
        combo_categorie = ttk.Combobox(frame_search, state="readonly")
        combo_categorie["values"] = [""] + [categorie[1] for categorie in categories]
        combo_categorie.grid(row=i // 4, column=(i % 4) * 2 + 1, padx=5, pady=5)
        combo_categorie.set("")
        entries[label] = combo_categorie
    elif label == "機器状況":
        combo_statuse = ttk.Combobox(frame_search, state="readonly")
        combo_statuse["values"] = [""] + [statuse[1] for statuse in statuses]
        combo_statuse.grid(row=i // 4, column=(i % 4) * 2 + 1, padx=5, pady=5)
        combo_statuse.set("")
        entries[label] = combo_statuse
    elif label == "部門":
        combo_department = ttk.Combobox(frame_search, state="readonly")
        combo_department["values"] = [""] + [department[1] for department in departments]
        combo_department.grid(row=i // 4, column=(i % 4) * 2 + 1, padx=5, pady=5)
        combo_department.set("")
        entries[label] = combo_department
    elif label == "部屋":
        combo_room = ttk.Combobox(frame_search, state="readonly")
        combo_room["values"] = [""] + [room[1] for room in rooms]
        combo_room.grid(row=i // 4, column=(i % 4) * 2 + 1, padx=5, pady=5)
        combo_room.set("")
        entries[label] = combo_room
    elif label == "製造元":
        combo_manufacturer = ttk.Combobox(frame_search, state="readonly")
        combo_manufacturer["values"] = [""] + [manufacturer[1] for manufacturer in manufacturers]
        combo_manufacturer.grid(row=i // 4, column=(i % 4) * 2 + 1, padx=5, pady=5)
        combo_manufacturer.set("")
        entries[label] = combo_manufacturer
    elif label == "販売元":
        combo_celler = ttk.Combobox(frame_search, state="readonly")
        combo_celler["values"] = [""] + [celler[1] for celler in cellers]
        combo_celler.grid(row=i // 4, column=(i % 4) * 2 + 1, padx=5, pady=5)
        combo_celler.set("")
        entries[label] = combo_celler
    else:
        entry = ttk.Entry(frame_search)
        entry.grid(row=i // 4, column=(i % 4) * 2 + 1, padx=5, pady=5)
        entries[label] = entry
# ボタン
btn_search = ttk.Button(frame_search, text="検索", command=search)
btn_search.grid(row=len(labels)//4+1, column=0, padx=5, pady=5)

btn_reset = ttk.Button(frame_search, text="条件初期化", command=reset_conditions)
btn_reset.grid(row=len(labels)//4+1, column=1, padx=5, pady=5)

# テーブル
tree = create_equipment_treeview(frame_table)
tree.grid(row=0, column=0, sticky="nsew")

# 縦スクロールバーの追加（右端に配置）
scrollbar_y = ttk.Scrollbar(frame_table, orient="vertical", command=tree.yview)
scrollbar_y.grid(row=0, column=1, sticky="ns")
tree.configure(yscrollcommand=scrollbar_y.set)

# 横スクロールバーの追加（下端に配置）
scrollbar_x = ttk.Scrollbar(frame_table, orient="horizontal", command=tree.xview)
scrollbar_x.grid(row=1, column=0, sticky="ew")
tree.configure(xscrollcommand=scrollbar_x.set)

# frame_table のグリッド配置設定
frame_table.grid_rowconfigure(0, weight=1)
frame_table.grid_columnconfigure(0, weight=1)

tree.bind("<Double-1>", on_tree_item_double_click)

root.mainloop()
