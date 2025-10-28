import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont
import subprocess
import json
import sqlite3
import os
import sys
from datetime import datetime
from repair_info import RepairInfoWindow
from equipment_sarch import fetch_data
from cls_master_data_fetcher import MasterDataFetcher
from open_master_list import open_master_list_window


class EquipmentManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("器材管理システム")
        self.root.geometry("1400x750")

        # JSON設定ファイルを読み込む
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        self.db_name = config.get("db_name", "equipment_management.db")
        self.fetcher = MasterDataFetcher(self.db_name)
        self.entries = {}

        self._load_master_data()
        self._create_widgets()
        self._create_menus()

    # ===== 共通ユーティリティ =====
    def clear_widget(self, widget):
        """Entry, Combobox, Text などの入力ウィジェットを安全にクリア"""
        if isinstance(widget, ttk.Combobox):
            widget.set("")
        elif isinstance(widget, tk.Text):
            widget.delete("1.0", tk.END)
        else:
            try:
                widget.delete(0, tk.END)
            except Exception:
                pass

    def get_widget_value(self, widget):
        """ウィジェットの値を安全に取得"""
        if isinstance(widget, ttk.Combobox):
            return widget.get().strip()
        elif isinstance(widget, tk.Text):
            return widget.get("1.0", "end-1c").strip()
        else:
            try:
                return widget.get().strip()
            except Exception:
                return ""

    def set_widget_value(self, widget, value):
        """ウィジェットに値を安全に設定"""
        if value is None:
            value = ""
        if isinstance(widget, ttk.Combobox):
            widget.set(value)
        elif isinstance(widget, tk.Text):
            widget.delete("1.0", tk.END)
            widget.insert("1.0", value)
        else:
            try:
                widget.delete(0, tk.END)
                widget.insert(0, value)
            except Exception:
                pass

    # ===== データ読込 =====
    def _load_master_data(self):
        self.categorys = self.fetcher.fetch_all("categorie_master") or [(1, "検査機器"), (2, "一般備品"), (3, "消耗品"), (4, "その他")]
        self.statuses = self.fetcher.fetch_all("statuse_master") or [(1, "使用中"), (2, "良好"), (3, "修理中"), (4, "廃棄")]
        self.departments = self.fetcher.fetch_all("department_master") or [(1, "検査科"), (2, "検体検査"), (3, "生理検査"), (4, "細菌検査"), (5, "病理検査"), (6, "採血室")]
        self.cellers = self.fetcher.fetch_all("celler_master") or []
        self.manufacturers = self.fetcher.fetch_all("manufacturer_master") or []
        self.rooms = self.fetcher.fetch_all("room_master") or [
            (1, "受付_染色室"), (2, "鏡検室"), (3, "臓器固定・切出室"), (4, "標本作製室"),
            (5, "病理標本保人室"), (6, "病理診断室"), (8, "剖検室"), (9, "剖検前室")
        ]

    # ===== メニュー作成 =====
    def _create_menus(self):
        menubar = tk.Menu(self.root)
        master_menu = tk.Menu(menubar, tearoff=0)

        for table in self._populate_master_menu():
            master_menu.add_command(
                label=table,
                command=lambda t=table: open_master_list_window(self.root, t)
            )

        menubar.add_cascade(label="マスタデータ", menu=master_menu)
        self.root.config(menu=menubar)

    def _populate_master_menu(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return tables

    # ===== メイン画面 =====
    def _create_widgets(self):
        self.root.option_add("*Font", ("MS UI Gothic", 11))

        frame_top = ttk.Frame(self.root)
        frame_top.pack(fill=tk.X, padx=10, pady=5)
        frame_search = ttk.Frame(self.root)
        frame_search.pack(fill=tk.X, padx=10, pady=5)
        frame_table = ttk.Frame(self.root)
        frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Label(frame_top, text="施設:").grid(row=0, column=0, padx=5, pady=5)
        entry_facility = ttk.Entry(frame_top)
        entry_facility.grid(row=0, column=1, padx=5, pady=5)
        entry_facility.insert(0, "0000000001 複十字病院　病理診断科")

        labels = ["機器分類", "機器コード", "機器名", "機器名カナ", "機器状況",
                  "部門", "部屋", "備考", "製造元", "販売元"]
        for i, label in enumerate(labels):
            ttk.Label(frame_search, text=label).grid(row=i//4, column=(i%4)*2, padx=5, pady=5)
            combo_values = []
            if label == "機器分類":
                combo_values = [c[1] for c in self.categorys]
            elif label == "機器状況":
                combo_values = [s[1] for s in self.statuses]
            elif label == "部門":
                combo_values = [d[1] for d in self.departments]
            elif label == "部屋":
                combo_values = [r[1] for r in self.rooms]
            elif label == "製造元":
                combo_values = [m[1] for m in self.manufacturers]
            elif label == "販売元":
                combo_values = [c[1] for c in self.cellers]

            if combo_values:
                combo = ttk.Combobox(frame_search, state="readonly", values=[""] + combo_values)
                combo.grid(row=i//4, column=(i%4)*2+1, padx=5, pady=5)
                self.entries[label] = combo
            else:
                entry = ttk.Entry(frame_search)
                entry.grid(row=i//4, column=(i%4)*2+1, padx=5, pady=5)
                self.entries[label] = entry

        ttk.Button(frame_search, text="検索", command=self.search).grid(row=3, column=0, padx=5, pady=5)
        ttk.Button(frame_search, text="条件初期化", command=self.reset_conditions).grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(frame_search, text="Excel出力", command=self.export_to_excel).grid(row=3, column=2, padx=5, pady=5)

        self.tree = self._create_treeview(frame_table)
        self.tree.bind("<Double-1>", self.open_repair_info)

        # 右クリックメニュー
        self.tree_menu = tk.Menu(self.root, tearoff=0)
        self.tree_menu.add_command(label="開く", command=self.open_repair_info)
        self.tree.bind("<Button-3>", self.show_tree_menu)

    # ===== イベント =====
    def show_tree_menu(self, event):
        """右クリックメニューを表示"""
        try:
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
                self.tree_menu.post(event.x_root, event.y_root)
        finally:
            self.tree_menu.grab_release()

    def open_repair_info(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], "values")
        equipment_code = values[1]  # 2列目に器材コード
        RepairInfoWindow(self.root, equipment_code)

    def reset_conditions(self):
        """全検索条件をリセット"""
        print("条件初期化")
        for widget in self.entries.values():
            self.clear_widget(widget)

    # ===== Treeview =====
    def _create_treeview(self, parent):
        columns = ["機器分類", "機器コード", "機器名", "状態", "部門", "部屋",
                   "製造元", "販売元", "備考", "購入日", "モデル"]
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="w")

        tree.tag_configure("evenrow", background="#F0F0FF")
        tree.tag_configure("oddrow", background="#FFFFFF")
        tree.grid(row=0, column=0, sticky="nsew")

        scrollbar_y = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scrollbar_y.set)

        scrollbar_x = ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        tree.configure(xscrollcommand=scrollbar_x.set)

        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        return tree

    # ===== 検索処理 =====
    def search(self):
        category_name = self.entries["機器分類"].get()
        category_id = next((id for id, name in self.categorys if name == category_name), None)

        status_name = self.entries["機器状況"].get()
        status_id = next((id for id, name in self.statuses if name == status_name), None)

        department_name = self.entries["部門"].get()
        department_id = next((id for id, name in self.departments if name == department_name), None)

        room_name = self.entries["部屋"].get()
        room_id = next((id for id, name in self.rooms if name == room_name), None)

        manufacturer_name = self.entries["製造元"].get()
        manufacturer_id = next((id for id, name in self.manufacturers if name == manufacturer_name), None)

        celler_name = self.entries["販売元"].get()
        celler_id = next((id for id, name in self.cellers if name == celler_name), None)

        equipment_code = self.entries["機器コード"].get()
        name = self.entries["機器名"].get()
        name_kana = self.entries["機器名カナ"].get()
        remarks = self.entries["備考"].get()

        try:
            records = fetch_data(equipment_code, name, name_kana, category_id, status_id,
                                 department_id, room_id, manufacturer_id, celler_id, remarks)
            if not records:
                messagebox.showinfo("情報", "該当するデータがありません。")
                return
            print(f"取得データ数 = {len(records)}")
        except Exception as e:
            print(f"fetch_data でエラー: {e}")
            messagebox.showerror("エラー", f"データ取得中にエラーが発生しました。\n{e}")
            return

        for row in self.tree.get_children():
            self.tree.delete(row)

        for index, record in enumerate(records):
            tag = "evenrow" if index % 2 == 0 else "oddrow"
            self.tree.insert("", tk.END, values=(
                next((n for i, n in self.categorys if i == record[4]), "不明"),
                record[1], record[2],
                next((n for i, n in self.statuses if i == record[5]), "不明"),
                next((n for i, n in self.departments if i == record[6]), "不明"),
                next((n for i, n in self.rooms if i == record[7]), "不明"),
                next((n for i, n in self.manufacturers if i == record[8]), "不明"),
                next((n for i, n in self.cellers if i == record[9]), "不明"),
                record[10], record[11], record[12]
            ), tags=(tag,))

    # ===== Excel出力 =====
    def export_to_excel(self):
        all_data = [self.tree.item(item, "values") for item in self.tree.get_children()]
        if not all_data:
            messagebox.showinfo("情報", "エクスポートするデータがありません。")
            return

        headers = ["機器分類", "機器コード", "機器名", "状態", "部門", "部屋",
                   "製造元", "販売元", "備考", "購入日", "モデル"]
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"export_{now_str}.xlsx"
        output_folder = r"C:\\desk_app\\export_files"

        json_data = json.dumps(all_data, ensure_ascii=False)
        json_headers = json.dumps(headers, ensure_ascii=False)

        subprocess.run(["python", "export_to_excel.py", json_data, json_headers, output_folder, file_name])


def main():
    try:
        root = tk.Tk()
        app = EquipmentManagerApp(root)
        root.mainloop()
    except Exception as e:
        import traceback
        traceback.print_exc()
        messagebox.showerror("実行エラー", f"アプリケーションでエラーが発生しました：\n{e}")


if __name__ == "__main__":
    main()
