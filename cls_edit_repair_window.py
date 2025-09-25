import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import filedialog, simpledialog
from tkcalendar import DateEntry
import sqlite3
from nullable_date_entry import NullableDateEntry

class EditRepairWindow(tk.Toplevel):
    def __init__(self, parent, db_name, equipment_id=None, repair_id=None, refresh_callback=None):
        super().__init__(parent)
        self.title("修理情報修正")
        self.db_name = db_name
        self.repair_id = repair_id
        self.refresh_callback = refresh_callback
        self.new_mode = (repair_id in (None, "", 0))   # ← ★ 新規判定s
        self.geometry("600x600")
        self.resizable(False, False)
        self.entries = {}
        self.equipment_id = equipment_id  # 修理情報に紐づく器材ID
        # マスタデータは常に取得
        self._fetch_masters()
        # データベースから修理情報・マスタデータを取得
        # 既存データ取得
        self.selected_data = None
        if not self.new_mode:
            self.selected_data = self.fetch_repair_data()
            if not self.selected_data:
                messagebox.showerror("エラー", f"ID={repair_id} の修理情報が見つかりません。")
                self.destroy()
                return
            self.equipment_id = self.selected_data.get("equipment_id", None)
        
        self.create_widgets()
        if self.selected_data:
            self.populate_fields()
    # --- マスタ取得だけ分離
    def _fetch_masters(self):
        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM repair_category_master")
            rows = cur.fetchall()
            self.categories = dict(rows) if rows else {}

            cur.execute("SELECT id, name FROM repair_status_master")
            rows = cur.fetchall()
            self.statuses = dict(rows) if rows else {}

            cur.execute("SELECT id, name FROM celler_master")
            rows = cur.fetchall()
            self.vendors = dict(rows) if rows else {}

    def fetch_repair_data(self):
        """repair_id に対応する修理情報とマスタデータを取得。"""
        if not self.repair_id:
            return None
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.row_factory = sqlite3.Row  # dict のように扱える
                cursor = conn.cursor()

                # 修理情報を取得
                cursor.execute("""
                    SELECT id, equipment_id, repairstatuses, repaircategories,
                        vendor, technician, request_date, completion_date, remarks
                    FROM repair
                    WHERE id = ?
                """, (self.repair_id,))
                row = cursor.fetchone()
                data = dict(row) if row else None

                if not data:
                    return None

                # 修理に紐づく器材IDを保存
                self.equipment_id = data["equipment_id"]  # ← ここを修正

                # 各種マスタ再取得
                cursor.execute("SELECT id, name FROM repair_category_master")
                self.categories = dict(cursor.fetchall())

                cursor.execute("SELECT id, name FROM repair_status_master")
                self.statuses = dict(cursor.fetchall())

                cursor.execute("SELECT id, name FROM celler_master")
                self.vendors = dict(cursor.fetchall())

                return data

        except Exception as e:
            messagebox.showerror("DBエラー", f"修理情報取得中にエラーが発生しました:\n{e}")
            return None

        
    def _display_attached_pdfs(self):
        """repair_id に紐づく PDF 一覧を表示する"""
        if not self.repair_id:
            return

        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("""
                SELECT name, doc_url FROM repair_document
                WHERE doc_repair_id = ?
                """, (self.repair_id,))
                pdfs = cur.fetchall()

            for i, (name, url) in enumerate(pdfs):
                label = tk.Label(self.pdf_frame, text=name, fg="blue", cursor="hand2", anchor="w", wraplength=150)
                label.grid(row=i, column=0, sticky="w")
                label.bind("<Button-1>", lambda e, path=url: self._open_pdf(path))

        except Exception as e:
            messagebox.showerror("PDF表示エラー", f"PDF一覧の取得中にエラーが発生:\n{e}")

            
    def create_widgets(self):
        labels = ["状態", "依頼日", "完了日", "カテゴリ", "業者", "技術者", "備考"]
        self.entries = {}

        for i, label in enumerate(labels):
            tk.Label(self, text=label).grid(row=i, column=0, padx=5, pady=5)

            if "日" in label:
                entry = NullableDateEntry(self, date_pattern="yyyy-mm-dd")
            elif label == "カテゴリ":
                entry = ttk.Combobox(self, values=list(self.categories.values()), state="readonly")
            elif label == "状態":
                entry = ttk.Combobox(self, values=list(self.statuses.values()), state="readonly")
            elif label == "業者":
                entry = ttk.Combobox(self, values=list(self.vendors.values()), state="readonly")
            elif label == "備考":
                entry = tk.Entry(self, width=40)
            else:
                entry = tk.Entry(self)

            entry.grid(row=i, column=1, padx=5, pady=5)
            self.entries[label] = entry


        # --- PDF 一覧のラベルフレームを右側に表示 ---
        self.pdf_frame = tk.LabelFrame(self, text="添付PDF一覧", padx=10, pady=10)
        self.pdf_frame.place(x=400, y=20, width=180, height=350)  # 右に配置

        if not self.new_mode:
            self._display_attached_pdfs()

            btn_frame = tk.Frame(self)
            btn_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)

            tk.Button(btn_frame, text="PDF添付", command=self._attach_pdf).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="保存", command=self.save_changes).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="キャンセル", command=self.destroy).pack(side=tk.LEFT, padx=5)



    def populate_fields(self):
        labels = ["状態", "依頼日", "完了日", "カテゴリ", "業者", "技術者", "備考"]
        if not self.selected_data:
            messagebox.showerror("エラー", "修理情報が取得できませんでした。")
            return
        
        # ID（int）で取得（カンマ不要）
        repairstatus_id = self.selected_data["repairstatuses"]
        category_id = self.selected_data["repaircategories"]
        vendor_id = self.selected_data["vendor"]

        values = [
            self.get_name_from_id(repairstatus_id, self.statuses),   # 状態
            self.selected_data["request_date"],                      # 依頼日
            self.selected_data["completion_date"],                   # 完了日
            self.get_name_from_id(category_id, self.categories),     # カテゴリ
            self.get_name_from_id(vendor_id, self.vendors),          # 業者
            self.selected_data["technician"],                        # 技術者
            self.selected_data["remarks"]                            # 備考
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

    def get_id_from_name(self, name: str, data_dict: dict) -> int | None:
        """名前からIDを取得（辞書型で）"""
        for item_id, item_name in data_dict.items():
            if item_name == name:
                return item_id
        return None

    def get_name_from_id(self, id: int, data_dict: dict) -> str:
        """IDから名前を取得（辞書型で）"""
        return data_dict.get(id, "")

    
    def _display_attached_pdfs(self):
        """equipment_id に紐づく PDF 一覧を表示する"""
        if not self.equipment_id:
            return

        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT name, doc_url FROM repair_document
                    WHERE doc_repair_id IN (
                        SELECT id FROM repair WHERE equipment_id = ?
                    )
                """, (self.equipment_id,))
                pdfs = cur.fetchall()

            for i, (name, url) in enumerate(pdfs):
                label = tk.Label(self.pdf_frame, text=name, fg="blue", cursor="hand2", anchor="w", wraplength=150)
                label.grid(row=i, column=0, sticky="w")
                label.bind("<Button-1>", lambda e, path=url: self._open_pdf(path))

        except Exception as e:
            messagebox.showerror("PDF表示エラー", f"PDF一覧の取得中にエラーが発生:\n{e}")
    
    def _open_pdf(self, path):
        """クリックでPDFを開く"""
        if not os.path.exists(path):
            messagebox.showwarning("ファイルなし", f"{path} が存在しません。")
            return
        try:
            if os.name == "nt":  # Windows
                os.startfile(path)
            elif os.name == "posix":
                subprocess.run(["xdg-open", path])
            else:
                messagebox.showinfo("未対応", "PDFの自動オープンはこのOSでは未対応です。")
        except Exception as e:
            messagebox.showerror("エラー", f"PDFの表示中にエラーが発生しました：\n{e}")

    # --- save_changes ----------
    def save_changes(self):
        new_values = {k: e.get() for k, e in self.entries.items()}

        repairstatus_id = self.get_id_from_name(new_values["状態"], self.statuses)
        category_id     = self.get_id_from_name(new_values["カテゴリ"], self.categories)
        vendor_id       = self.get_id_from_name(new_values["業者"], self.vendors)

        if None in (repairstatus_id, category_id, vendor_id):
            messagebox.showerror("エラー", "マスタの選択値が不正です。")
            return

        try:
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()

                if self.new_mode:
                    # ★ 新規追加：id を MAX(id)+1 で採番
                    cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM repair")
                    new_id = cur.fetchone()[0]

                    cur.execute("""
                        INSERT INTO repair
                        (id, equipment_id, repairstatuses, request_date, completion_date,
                         repaircategories, vendor, technician, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        new_id,
                        self.equipment_id,
                        repairstatus_id,
                        new_values["依頼日"],
                        new_values["完了日"],
                        category_id,
                        vendor_id,
                        new_values["技術者"],
                        new_values.get("備考", "")
                    ))
                else:
                    # 既存更新
                    cur.execute("""
                        UPDATE repair
                        SET repairstatuses=?, request_date=?, completion_date=?,
                            repaircategories=?, vendor=?, technician=?
                        WHERE id=?
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

            msg = "修理情報を追加しました。" if self.new_mode else "修理情報を更新しました。"
            messagebox.showinfo("完了", msg)
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()

        except Exception as e:
            messagebox.showerror("DBエラー", str(e))