import os
import shutil
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from nullable_date_entry import NullableDateEntry
from datetime import datetime
from tkinter import simpledialog


class EditRepairWindow(tk.Toplevel):
    FIELD_LABELS = ["状態", "依頼日", "完了日", "対応", "業者", "技術者", "詳細", "備考"]

    def __init__(self, parent, db_name, equipment_code=None, repair_id=None, refresh_callback=None):
        super().__init__(parent)
        self.title("修理情報 編集ウィンドウ")
        self.geometry("650x600")

        self.db_name = db_name
        self.equipment_code = equipment_code
        self.repair_id = repair_id
        self.refresh_callback = refresh_callback
        self.entries = {}

        # === マスター取得 ===
        self.statuses = self.fetch_master("repair_statuse_master")
        self.types = self.fetch_master("repair_type_master")
        self.vendors = self.fetch_master("celler_master")

        # === 画面構築 ===
        self._create_widgets()

        if repair_id:
            self.load_repair_data(repair_id)
            self.load_pdf_list()

    # ========= マスター読込 =========
    def fetch_master(self, table_name):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT id, name FROM {table_name}")
                return dict(cursor.fetchall())
        except Exception as e:
            print(f"マスター取得エラー({table_name}): {e}")
            return {}

    # ========= 共通関数 =========
    def get_widget_value(self, widget):
        if isinstance(widget, ttk.Combobox):
            return widget.get().strip()
        elif isinstance(widget, tk.Text):
            return widget.get("1.0", "end-1c").strip()
        elif isinstance(widget, (tk.Entry, NullableDateEntry, DateEntry)):
            return widget.get().strip()
        return ""

    def set_widget_value(self, widget, value):
        if isinstance(widget, (DateEntry, NullableDateEntry)):
            try:
                if value:
                    widget.set_date(value)
                else:
                    widget.delete(0, tk.END)
            except:
                widget.delete(0, tk.END)
        elif isinstance(widget, ttk.Combobox):
            widget.set(value)
        elif isinstance(widget, tk.Text):
            widget.delete("1.0", tk.END)
            widget.insert("1.0", value)
        else:
            widget.delete(0, tk.END)
            widget.insert(0, value)

    # ========= ウィジェット作成 =========
    def _create_widgets(self):
        frame_top = tk.Frame(self)
        frame_top.pack(pady=10)

        for i, label in enumerate(self.FIELD_LABELS):
            tk.Label(frame_top, text=label).grid(row=i, column=0, padx=5, pady=3, sticky="e")

            if "日" in label:
                entry = NullableDateEntry(frame_top, date_pattern="yyyy-mm-dd")
            elif label == "対応":
                entry = ttk.Combobox(frame_top, values=list(self.types.values()), state="readonly")
            elif label == "状態":
                entry = ttk.Combobox(frame_top, values=list(self.statuses.values()), state="readonly")
            elif label == "業者":
                entry = ttk.Combobox(frame_top, values=list(self.vendors.values()), state="readonly")
            elif label in ("詳細", "備考"):
                entry = tk.Text(frame_top, width=40, height=3)
            else:
                entry = tk.Entry(frame_top, width=40)

            entry.grid(row=i, column=1, padx=5, pady=3, sticky="w")
            self.entries[label] = entry

        # --- ボタン群を別メソッドで作成 ---
        self._create_buttons()

        # === PDF一覧 ===
        frame_pdf = tk.LabelFrame(self, text="添付PDF一覧")
        frame_pdf.pack(fill="both", expand=True, padx=10, pady=10)

        self.pdf_listbox = tk.Listbox(frame_pdf, height=6)
        self.pdf_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.pdf_listbox.bind("<Double-Button-1>", self.open_selected_pdf)

    def _create_buttons(self):
        """保存・PDF添付・戻るボタン群を作成"""
        frame_btn = tk.Frame(self)
        frame_btn.pack(pady=10)

        btn_save = tk.Button(frame_btn, text="保存", width=12, command=self.save_changes)
        btn_pdf = tk.Button(frame_btn, text="PDF添付", width=12, command=self.attach_pdf)
        btn_cancel = tk.Button(frame_btn, text="保存せずに戻る", width=15, command=self.cancel_and_close)

        btn_save.pack(side="left", padx=10)
        btn_pdf.pack(side="left", padx=10)
        btn_cancel.pack(side="left", padx=10)

    def cancel_and_close(self):
        """保存せずに閉じる"""
        #if messagebox.askyesno("確認", "変更を保存せずに閉じますか？"):
        self.destroy()

    # ========= 修理情報の読込 =========
    def load_repair_data(self, repair_id):
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT repairstatuses, request_date, completion_date, repairtype, vendor,
                           technician, details, remarks
                    FROM repair WHERE id = ?
                """, (repair_id,))
                data = cursor.fetchone()

            if not data:
                messagebox.showerror("エラー", "修理情報が見つかりません。")
                return

            keys = ["状態", "依頼日", "完了日", "対応", "業者", "技術者", "詳細", "備考"]
            for key, value in zip(keys, data):
                self.set_widget_value(self.entries[key], self.get_name_from_id(value, key))
        except Exception as e:
            messagebox.showerror("読込エラー", f"修理情報読込中にエラーが発生しました:\n{e}")

    # ========= 保存 =========
    def save_changes(self):
        try:
            new_values = {k: self.get_widget_value(w) for k, w in self.entries.items()}
            repairstatus_id = self.get_id_from_name(new_values["状態"], self.statuses)
            repairtype_id = self.get_id_from_name(new_values["対応"], self.types)
            vendor_id = self.get_id_from_name(new_values["業者"], self.vendors)

            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                if self.repair_id:  # 更新
                    cursor.execute("""
                        UPDATE repair
                        SET repairstatuses=?, request_date=?, completion_date=?,
                            repairtype=?, vendor=?, technician=?, details=?, remarks=?
                        WHERE id=?
                    """, (
                        repairstatus_id, new_values["依頼日"], new_values["完了日"],
                        repairtype_id, vendor_id, new_values["技術者"],
                        new_values["詳細"], new_values["備考"], self.repair_id
                    ))
                else:  # 新規
                    cursor.execute("""
                        INSERT INTO repair
                        (equipment_code, repairstatuses, request_date, completion_date,
                         repairtype, vendor, technician, details, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.equipment_code, repairstatus_id, new_values["依頼日"], new_values["完了日"],
                        repairtype_id, vendor_id, new_values["技術者"],
                        new_values["詳細"], new_values["備考"]
                    ))
                    self.repair_id = cursor.lastrowid

                conn.commit()

            messagebox.showinfo("保存完了", "修理情報を保存しました。")
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("保存エラー", f"修理情報保存中にエラーが発生しました:\n{e}")
    
    def save_changes_without_close(self):
        """修理情報を保存するがウィンドウを閉じない（PDF添付用）"""
        try:
            new_values = {k: self.get_widget_value(w) for k, w in self.entries.items()}
            repairstatus_id = self.get_id_from_name(new_values["状態"], self.statuses)
            repairtype_id = self.get_id_from_name(new_values["対応"], self.types)
            vendor_id = self.get_id_from_name(new_values["業者"], self.vendors)

            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                if self.repair_id:  # 既存修理データを更新
                    cursor.execute("""
                        UPDATE repair
                        SET repairstatuses=?, request_date=?, completion_date=?,
                            repairtype=?, vendor=?, technician=?, details=?, remarks=?
                        WHERE id=?
                    """, (
                        repairstatus_id, new_values["依頼日"], new_values["完了日"],
                        repairtype_id, vendor_id, new_values["技術者"],
                        new_values["詳細"], new_values["備考"], self.repair_id
                    ))
                else:  # 新規修理データを追加
                    cursor.execute("""
                        INSERT INTO repair
                        (equipment_code, repairstatuses, request_date, completion_date,
                         repairtype, vendor, technician, details, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        self.equipment_code, repairstatus_id, new_values["依頼日"], new_values["完了日"],
                        repairtype_id, vendor_id, new_values["技術者"],
                        new_values["詳細"], new_values["備考"]
                    ))
                    self.repair_id = cursor.lastrowid

                conn.commit()

            # ウィンドウは閉じず、リロードのみ行う
            if self.refresh_callback:
                self.refresh_callback()

        except Exception as e:
            messagebox.showerror("保存エラー", f"修理情報保存中にエラーが発生しました:\n{e}")


    # ========= PDF添付 =========
    def attach_pdf(self):
        """PDFファイル添付（保存＋データ更新＋リスト更新）"""
        # まず現在の編集内容を保存
        try:
            self.save_changes_without_close()
        except Exception as e:
            messagebox.showerror("保存エラー", f"保存中にエラーが発生しました:\n{e}")
            return

        if not self.repair_id:
            messagebox.showwarning("注意", "PDFを添付するには、修理情報を先に保存してください。")
            return

        # ファイル選択
        file_path = filedialog.askopenfilename(
            title="PDFを選択", filetypes=[("PDFファイル", "*.pdf")]
        )
        if not file_path:
            return
        
        # === ファイル名入力 ===
        default_name = os.path.basename(file_path)
        new_name = simpledialog.askstring(
            "ファイル名入力",
            f"保存するPDFファイル名を入力してください（拡張子 .pdf は自動で付きます）:",
            initialvalue=os.path.splitext(default_name)[0],
            parent=self
        )

        if not new_name:  # キャンセルされた場合
            return

        # 拡張子付ける
        if not new_name.lower().endswith(".pdf"):
            new_name += ".pdf"


        try:
            # 添付先ディレクトリ
            save_dir = os.path.join("attached_pdfs", str(self.repair_id))
            os.makedirs(save_dir, exist_ok=True)

            # 保存パス
            save_path = os.path.join(save_dir, new_name)

            # ファイルコピー
            shutil.copy(file_path, save_path)

            messagebox.showinfo("完了", f"PDFを添付しました。\n{save_path}")

            # === PDFリスト再読み込み ===
            self.load_pdf_list()

            # === 修理データ再読込（更新反映） ===
            self.load_repair_data(self.repair_id)

            # ウィンドウを前面に
            self.lift()
            self.focus_force()

        except Exception as e:
            messagebox.showerror("添付エラー", f"PDF添付中にエラーが発生しました:\n{e}")


    # ========= PDF一覧読込 =========
    def load_pdf_list(self):
        """添付済みPDFを一覧表示"""
        self.pdf_listbox.delete(0, tk.END)
        pdf_dir = os.path.join("attached_pdfs", str(self.repair_id))
        if os.path.exists(pdf_dir):
            pdfs = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
            for pdf in pdfs:
                self.pdf_listbox.insert(tk.END, pdf)

    # ========= PDFダブルクリック開く =========
    def open_selected_pdf(self, event=None):
        """選択中のPDFを開く"""
        selection = self.pdf_listbox.curselection()
        if not selection:
            return
        file_name = self.pdf_listbox.get(selection[0])
        pdf_path = os.path.join("attached_pdfs", str(self.repair_id), file_name)
        try:
            os.startfile(pdf_path)
        except Exception as e:
            messagebox.showerror("エラー", f"PDFを開けませんでした:\n{e}")

    # ========= ID・名称変換 =========
    def get_name_from_id(self, id_value, key):
        mapping = {"状態": self.statuses, "対応": self.types, "業者": self.vendors}
        return mapping.get(key, {}).get(id_value, id_value or "")

    def get_id_from_name(self, name, mapping):
        for id_, nm in mapping.items():
            if nm == name:
                return id_
        return None
