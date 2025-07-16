import os
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter import filedialog, simpledialog
from tkcalendar import DateEntry
import sqlite3
from nullable_date_entry import NullableDateEntry

class EditRepairWindow(tk.Toplevel):
    def __init__(self, parent, db_name, equipment_id=None, repair_id="", refresh_callback=None):
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
            self.categories = cur.fetchall()
            cur.execute("SELECT id, name FROM repair_status_master")
            self.statuses = cur.fetchall()
            cur.execute("SELECT id, name FROM celler_master")
            self.vendors = cur.fetchall()

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
        
    def _attach_pdf(self):
        """PDF を選択 → 文書名入力 → repair_document テーブルへ INSERT"""
        # ファイル選択ダイアログ
        pdf_path = filedialog.askopenfilename(
            parent=self, title="PDF を選択",
            filetypes=[("PDF ファイル", "*.pdf")])
        if not pdf_path:
            return  # キャンセル

        # 文書名入力
        doc_name = simpledialog.askstring("文書名入力", "添付文書名を入力してください：", parent=self)
        if not doc_name:
            messagebox.showwarning("入力なし", "文書名が空です。")
            return

        # 新規追加モードでまだ保存していない場合は警告
        if self.new_mode:
            messagebox.showinfo("先に保存を", "修理レコードを先に保存してから PDF を添付してください。")
            return

        # ファイルの保存先 URL を作成（例：アプリ配下の docs フォルダにコピー）
        docs_dir = os.path.join(os.getcwd(), "docs")
        os.makedirs(docs_dir, exist_ok=True)
        dest_path = os.path.join(docs_dir, os.path.basename(pdf_path))
        try:
            # 同名なら上書きコピー
            import shutil
            shutil.copy2(pdf_path, dest_path)

            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO repair_document (name, doc_repair_id, doc_url)
                    VALUES (?, ?, ?)
                """, (doc_name, self.repair_id, dest_path))
                conn.commit()

            messagebox.showinfo("完了", "PDF を添付しました。")
        except Exception as e:
            messagebox.showerror("DBエラー", f"PDF 添付中にエラーが発生：\n{e}")
            
    def create_widgets(self):
        labels = ["状態", "依頼日", "完了日", "カテゴリ", "業者", "技術者", "備考"]
        self.entries = {}

        for i, label in enumerate(labels):
            tk.Label(self, text=label).grid(row=i, column=0, padx=5, pady=5)

            if "日" in label:
                entry = NullableDateEntry(self, date_pattern="yyyy-mm-dd")
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
                        SELECT id FROM repair_table WHERE equipment_id = ?
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