import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from datetime import datetime
from tkinter import simpledialog

# Model層から必要なクラスをインポート
from models.master_model import MasterModel
from models.repair_model import RepairModel


class NullableDateEntry(DateEntry):
    """
    空白を許容し、日付が未設定でも使える DateEntry 拡張クラス。
    - 空欄で初期化・表示が可能
    - 手入力で日付を削除可能
    - 無効な日付は赤文字で警告
    """
    def __init__(self, master=None, **kwargs):
        self._date_pattern = kwargs.get("date_pattern", "yyyy-mm-dd")
        self._default_fg = kwargs.get("foreground", "black")

        super().__init__(master, **kwargs)

        self._var = self["textvariable"] or tk.StringVar()
        self.configure(textvariable=self._var)
        self._var.trace_add("write", self._on_write)

    def _on_write(self, *args):
        value = self._var.get().strip()
        if not value:
            self.configure(foreground=self._default_fg)
            return
        try:
            datetime.strptime(value, self._date_pattern.replace("yyyy", "%Y").replace("mm", "%m").replace("dd", "%d"))
            self.configure(foreground=self._default_fg)
        except ValueError:
            self.configure(foreground="red")

    def get(self):
        value = super().get().strip()
        return "" if not value else value

    def set_date(self, value):
        if not value:
            self.delete(0, tk.END)
        else:
            super().set_date(value)


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

        # モーダルに設定（親画面の操作をロック）
        self.grab_set()

        # === マスター取得 ===
        self.statuses = MasterModel.get_kv_lookup("repair_statuse_master")
        self.types = MasterModel.get_kv_lookup("repair_type_master")
        self.vendors = MasterModel.get_kv_lookup("celler_master")

        # === 画面構築 ===
        self._create_widgets()

        if self.repair_id:
            self.load_repair_data(self.repair_id)
            self.load_pdf_list()
        else:
            # 新規登録時は依頼日に今日の日付をデフォルトセット
            self.set_widget_value(self.entries["依頼日"], datetime.now().strftime("%Y-%m-%d"))

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
                try:
                    widget.delete(0, tk.END)
                except:
                    pass
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

            # 提案いただいた NullableDateEntry を依頼日・完了日の両方に適応！
            if "日" in label:
                entry = NullableDateEntry(frame_top, date_pattern="yyyy-mm-dd", width=38)
            elif label == "対応":
                entry = ttk.Combobox(frame_top, values=list(self.types.values()), state="readonly", width=37)
            elif label == "状態":
                entry = ttk.Combobox(frame_top, values=list(self.statuses.values()), state="readonly", width=37)
            elif label == "業者":
                entry = ttk.Combobox(frame_top, values=list(self.vendors.values()), state="readonly", width=37)
            elif label in ("詳細", "備考"):
                entry = tk.Text(frame_top, width=40, height=3)
            else:
                entry = tk.Entry(frame_top, width=40)

            entry.grid(row=i, column=1, padx=5, pady=3, sticky="w")
            self.entries[label] = entry

        # --- ボタン群を作成 ---
        self._create_buttons()

        # === PDF一覧 ===
        frame_pdf = tk.LabelFrame(self, text="添付PDF一覧")
        frame_pdf.pack(fill="both", expand=True, padx=10, pady=10)

        self.pdf_listbox = tk.Listbox(frame_pdf, height=6)
        self.pdf_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.pdf_listbox.bind("<Double-Button-1>", self.open_selected_pdf)

    def _create_buttons(self):
        frame_btn = tk.Frame(self)
        frame_btn.pack(pady=10)

        btn_save = tk.Button(frame_btn, text="保存", width=12, command=self.save_changes)
        btn_pdf = tk.Button(frame_btn, text="PDF添付", width=12, command=self.attach_pdf)
        btn_cancel = tk.Button(frame_btn, text="保存せずに戻る", width=15, command=self.cancel_and_close)

        btn_save.pack(side="left", padx=10)
        btn_pdf.pack(side="left", padx=10)
        btn_cancel.pack(side="left", padx=10)

    def cancel_and_close(self):
        self.destroy()

    # ========= 修理情報の読込 =========
    def load_repair_data(self, repair_id):
        try:
            import sqlite3
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

    # ========= 保存処理の実体 =========
    def execute_db_save(self):
        new_values = {k: self.get_widget_value(w) for k, w in self.entries.items()}
        repairstatus_id = self.get_id_from_name(new_values["状態"], self.statuses)
        repairtype_id = self.get_id_from_name(new_values["対応"], self.types)
        vendor_id = self.get_id_from_name(new_values["業者"], self.vendors)

        # 「依頼日」に入力された文字が赤く反転している(不正入力)状態、または未入力の時は弾く
        if self.entries["依頼日"].cget("foreground") == "red" or not new_values["依頼日"]:
            messagebox.showwarning("入力チェック", "「依頼日」が正しく入力されていません。")
            raise ValueError("不正な日付")
            
        if self.entries["完了日"].get() and self.entries["完了日"].cget("foreground") == "red":
            messagebox.showwarning("入力チェック", "「完了日」の形式が正しくありません。")
            raise ValueError("不正な日付")

        if not (repairstatus_id and repairtype_id and vendor_id):
            messagebox.showwarning("入力チェック", "「状態」「対応」「業者」は必須項目です。")
            raise ValueError("必須項目未入力")

        import sqlite3
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            if self.repair_id:
                cursor.execute("""
                    UPDATE repair
                    SET repairstatuses=?, request_date=?, completion_date=?,
                        repairtype=?, vendor=?, technician=?, details=?, remarks=?
                    WHERE id=?
                """, (
                    repairstatus_id, new_values["依頼日"], new_values["完了日"] if new_values["完了日"] else None,
                    repairtype_id, vendor_id, new_values["技術者"] if new_values["技術者"] else None,
                    new_values["詳細"] if new_values["詳細"] else None, new_values["備考"] if new_values["備考"] else None, self.repair_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO repair
                    (equipment_code, repairstatuses, request_date, completion_date,
                     repairtype, vendor, technician, details, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.equipment_code, repairstatus_id, new_values["依頼日"], new_values["完了日"] if new_values["完了日"] else None,
                    repairtype_id, vendor_id, new_values["技術者"] if new_values["技術者"] else None,
                    new_values["詳細"] if new_values["詳細"] else None, new_values["備考"] if new_values["備考"] else None
                ))
                self.repair_id = cursor.lastrowid
            conn.commit()

    def save_changes(self):
        try:
            self.execute_db_save()
            messagebox.showinfo("保存完了", "修理情報を保存しました。")
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
        except ValueError:
            pass
        except Exception as e:
            messagebox.showerror("保存エラー", f"修理情報保存中にエラーが発生しました:\n{e}")
    
    def save_changes_without_close(self):
        self.execute_db_save()
        if self.refresh_callback:
            self.refresh_callback()

    # ========= PDF添付 =========
    def attach_pdf(self):
        try:
            self.save_changes_without_close()
        except ValueError:
            return
        except Exception as e:
            messagebox.showerror("保存エラー", f"保存中にエラーが発生しました:\n{e}")
            return

        if not self.repair_id:
            messagebox.showwarning("注意", "PDFを添付するには、修理情報を先に保存してください。")
            return

        file_path = filedialog.askopenfilename(title="PDFを選択", filetypes=[("PDFファイル", "*.pdf")])
        if not file_path:
            return
        
        default_name = os.path.basename(file_path)
        new_name = simpledialog.askstring(
            "ファイル名入力",
            f"保存するPDFファイル名を入力してください（拡張子 .pdf は自動で付きます）:",
            initialvalue=os.path.splitext(default_name)[0],
            parent=self
        )
        if not new_name:
            return

        if not new_name.lower().endswith(".pdf"):
            new_name += ".pdf"

        try:
            save_dir = os.path.join("attached_pdfs", str(self.repair_id))
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, new_name)
            shutil.copy(file_path, save_path)

            messagebox.showinfo("完了", f"PDFを添付しました。\n{save_path}")
            self.load_pdf_list()
            self.load_repair_data(self.repair_id)

            self.lift()
            self.focus_force()
        except Exception as e:
            messagebox.showerror("添付エラー", f"PDF添付中にエラーが発生しました:\n{e}")

    # ========= PDF一覧読込 =========
    def load_pdf_list(self):
        self.pdf_listbox.delete(0, tk.END)
        pdf_dir = os.path.join("attached_pdfs", str(self.repair_id))
        if os.path.exists(pdf_dir):
            pdfs = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
            for pdf in pdfs:
                self.pdf_listbox.insert(tk.END, pdf)

    # ========= PDFダブルクリック開く =========
    def open_selected_pdf(self, event=None):
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