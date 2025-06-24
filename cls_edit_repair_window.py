import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import DateEntry
import sqlite3

class EditRepairWindow(tk.Toplevel):
    def __init__(self, parent, db_name, repair_id, equipment_id, categories, statuses, vendors, refresh_callback=None):
        super().__init__(parent)
        self.title("修理情報修正")
        self.db_name = db_name
        self.repair_id = repair_id
        self.equipment_id = equipment_id
        self.categories = categories  # [(id, name), ...]
        self.statuses = statuses      # [(id, name), ...]
        self.vendors = vendors        # [(id, name), ...]
        self.refresh_callback = refresh_callback

        # データベースから修理情報を取得
        self.selected_data = self.fetch_repair_data()

        if not self.selected_data:
            messagebox.showerror("エラー", f"ID={repair_id} の修理情報が見つかりません。")
            self.destroy()
            return

        self.create_widgets()
        self.populate_fields()

    def fetch_repair_data(self):
        """repair_id に対応する修理情報をデータベースから取得する。"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, equipment_id, repairstatuses, repaircategories,
                           vendor, technician, request_date, completion_date, remarks
                    FROM repair
                    WHERE id = ?
                """, (self.repair_id,))
                return cursor.fetchone()
        except Exception as e:
            messagebox.showerror("DBエラー", f"修理情報取得中にエラーが発生しました:\n{e}")
            return None

    def create_widgets(self):
        labels = ["状態", "依頼日", "完了日", "カテゴリ", "業者", "技術者"]
        self.entries = {}

        for i, label in enumerate(labels):
            tk.Label(self, text=label).grid(row=i, column=0, padx=5, pady=5)

            if "日" in label:
                entry = DateEntry(self, date_pattern='yyyy-mm-dd')
            elif label == "カテゴリ":
                category_names = [name for _, name in self.categories]
                entry = ttk.Combobox(self, values=category_names, state="readonly")
            elif label == "業者":
                vendor_names = [name for _, name in self.vendors]
                entry = ttk.Combobox(self, values=vendor_names, state="readonly")
            else:
                entry = tk.Entry(self)

            entry.grid(row=i, column=1, padx=5, pady=5)
            self.entries[label] = entry

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="保存", command=self.save_changes).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="キャンセル", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def populate_fields(self):
        if not self.selected_data:
            messagebox.showerror("エラー", "修理情報が選択されていません。")
            self.destroy()
            return

        labels = ["状態", "依頼日", "完了日", "カテゴリ", "業者", "技術者"]
        for key, value in zip(labels, self.selected_data):
            widget = self.entries.get(key)
            if widget:
                if isinstance(widget, DateEntry):
                    if value:
                        widget.set_date(value)
                elif isinstance(widget, ttk.Combobox):
                    widget.set(value)
                else:
                    widget.delete(0, tk.END)
                    widget.insert(0, value)

    def get_id_from_name(self, name, data_list):
        """選択名に対応するIDを返す。該当しなければNone。"""
        for item_id, item_name in data_list:
            if item_name == name:
                return item_id
        return None

    def save_changes(self):
        new_values = {key: entry.get() for key, entry in self.entries.items()}

        # カテゴリ名と業者名 → IDに変換
        
        category_id = self.get_id_from_name(new_values["カテゴリ"], self.categories)
        vendor_id = self.get_id_from_name(new_values["業者"], self.vendors)

        if category_id is None or vendor_id is None:
            messagebox.showerror("エラー", "カテゴリまたは業者が無効です。")
            return

        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE repair
                SET repairstatuses = ?, request_date = ?, completion_date = ?,
                    repaircategories = ?, vendor = ?, technician = ?
                    WHERE id = ?
            """, (
                new_values["状態"],
                new_values["依頼日"],
                new_values["完了日"],
                category_id,
                vendor_id,
                new_values["技術者"],
                self.repair_id
            ))

            conn.commit()
            conn.close()
            messagebox.showinfo("完了", "修理情報を更新しました。")
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()

        except Exception as e:
            messagebox.showerror("エラー", f"データベース更新中にエラーが発生しました: {e}")
