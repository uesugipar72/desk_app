import tkinter as tk
from tkinter import messagebox, ttk
from tkcalendar import DateEntry
import sqlite3

class EditRepairWindow(tk.Toplevel):
    def __init__(self, parent, db_name, repair_id, refresh_callback=None):
        super().__init__(parent)
        self.title("修理情報修正")
        self.db_name = db_name
        self.repair_id = repair_id
        self.refresh_callback = refresh_callback

        # データベースから修理情報・マスタデータを取得
        self.selected_data = self.fetch_repair_data()

        if not self.selected_data:
            messagebox.showerror("エラー", f"ID={repair_id} の修理情報が見つかりません。")
            self.destroy()
            return

        self.create_widgets()
        self.populate_fields()

    def fetch_repair_data(self):
        """repair_id に対応する修理情報とマスタデータを取得。"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                # 修理情報を取得
                cursor.execute("""
                    SELECT id, equipment_id, repairstatuses, repaircategories,
                           vendor, technician, request_date, completion_date, remarks
                    FROM repair
                    WHERE id = ?
                """, (self.repair_id,))
                data = cursor.fetchone()

                if not data:
                    return None

                # 各種マスタデータを取得
                self.equipment_id = data[1]

                cursor.execute("SELECT id, name FROM repair_category_master")
                self.categories = cursor.fetchall()

                cursor.execute("SELECT id, name FROM repair_status_master")
                self.statuses = cursor.fetchall()

                cursor.execute("SELECT id, name FROM celler_master")
                self.vendors = cursor.fetchall()
                
                return data
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
                entry = ttk.Combobox(self, values=[name for _, name in self.categories], state="readonly")
            elif label == "状態":
                entry = ttk.Combobox(self, values=[name for _, name in self.statuses], state="readonly")
            elif label == "業者":
                entry = ttk.Combobox(self, values=[name for _, name in self.vendors], state="readonly")
            else:
                entry = tk.Entry(self)

            entry.grid(row=i, column=1, padx=5, pady=5)
            self.entries[label] = entry

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="保存", command=self.save_changes).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="キャンセル", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def populate_fields(self):
        labels = ["状態", "依頼日", "完了日", "カテゴリ", "業者", "技術者", "備考"]
        if not self.selected_data:
            messagebox.showerror("エラー", "修理情報が取得できませんでした。")
            return
        repairstatus_id, category_id, vendor_id = self.selected_data[2], self.selected_data[3], self.selected_data[4]

        values = [
            self.get_name_from_id(repairstatus_id, self.statuses),   # 状態
            self.selected_data[6],                                   # 依頼日
            self.selected_data[7],                                   # 完了日
            self.get_name_from_id(category_id, self.categories),     # カテゴリ           
            self.get_name_from_id(vendor_id, self.vendors),           # 業者
            self.selected_data[5],                                   # 技術者
        ]

        for key, value in zip(labels, values):
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
        for item_id, item_name in data_list:
            if item_name == name:
                return item_id
        return None

    def get_name_from_id(self, id, data_list):
        for item_id, item_name in data_list:
            if item_id == id:
                return item_name
        return ""

    def save_changes(self):
        new_values = {key: entry.get() for key, entry in self.entries.items()}

        repairstatus_id = self.get_id_from_name(new_values["状態"], self.statuses)
        category_id = self.get_id_from_name(new_values["カテゴリ"], self.categories)
        vendor_id = self.get_id_from_name(new_values["業者"], self.vendors)

        if repairstatus_id is None or category_id is None or vendor_id is None:
            messagebox.showerror("エラー", "マスタの選択値が不正です。")
            return

        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE repair
                    SET repairstatuses = ?, request_date = ?, completion_date = ?,
                        repaircategories = ?, vendor = ?, technician = ?
                    WHERE id = ?
                """, (
                    repairstatus_id,
                    new_values["依頼日"],
                    new_values["完了日"],
                    category_id,
                    vendor_id,
                    new_values["技術者"],
                    self.repair_id
                ))
                conn.commit()

            messagebox.showinfo("完了", "修理情報を更新しました。")
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()

        except Exception as e:
            messagebox.showerror("エラー", f"データベース更新中にエラーが発生しました: {e}")
