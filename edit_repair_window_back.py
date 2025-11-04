import os
import shutil
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
from nullable_date_entry import NullableDateEntry
from datetime import datetime
from tkinter import filedialog, simpledialog, messagebox

class EditRepairWindow(tk.Toplevel):
    FIELD_LABELS = ["状態", "依頼日", "完了日", "対応", "業者", "技術者", "詳細", "備考"]

    def __init__(self, parent, db_name, equipment_code=None, repair_id=None, refresh_callback=None):
        super().__init__(parent)
        self.title("修理情報 編集ウィンドウ")
        self.geometry("600x500")

        self.db_name = db_name
        self.equipment_code = equipment_code
        self.repair_id = repair_id
        self.refresh_callback = refresh_callback
        self.entries = {}

        # === マスター取得 ===
        self.statuses = self.fetch_master("repair_statuse_master")
        self.types = self.fetch_master("repair_type_master")
        self.vendors = self.fetch_master("celler_master")

        self._create_widgets()

        if repair_id:
            self.load_repair_data(repair_id)

    # ========= マスター読込 =========
    def fetch_master(self, table_name):
        """マスターデータ（id→name辞書）を取得"""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT id, name FROM {table_name}")
                return dict(cursor.fetchall())
        except Exception as e:
            print(f"マスター取得エラー({table_name}): {e}")
            return {}

    # ========= 共通ウィジェット関数 =========
    def clear_widget(self, widget):
        """ウィジェットを安全にクリア"""
        if isinstance(widget, ttk.Combobox):
            widget.set("")
        elif isinstance(widget, tk.Text):
            widget.delete("1.0", tk.END)
        elif isinstance(widget, (tk.Entry, NullableDateEntry, DateEntry)):
            widget.delete(0, tk.END)
        else:
            pass

    def get_widget_value(self, widget):
        """ウィジェットの値を安全に取得"""
        try:
            if isinstance(widget, ttk.Combobox):
                return widget.get().strip()
            elif isinstance(widget, tk.Text):
                return widget.get("1.0", "end-1c").strip()
            elif isinstance(widget, (tk.Entry, NullableDateEntry, DateEntry)):
                val = widget.get().strip()
                return val if val not in ("", "None", "0000-00-00") else None
            else:
                return ""
        except Exception:
            return ""

    def set_widget_value(self, widget, value):
        """ウィジェットに値を安全に設定（DateEntry対応）"""
        if value in (None, "", "0000-00-00", "None"):
            value = ""

        # DateEntry / NullableDateEntry
        if isinstance(widget, (DateEntry, NullableDateEntry)):
            try:
                if value:
                    widget.set_date(value)
                else:
                    widget.delete(0, tk.END)
            except Exception:
                widget.delete(0, tk.END)
            return

        # Combobox
        if isinstance(widget, ttk.Combobox):
            widget.set(value)
            return

        # Text
        if isinstance(widget, tk.Text):
            widget.delete("1.0", tk.END)
            widget.insert("1.0", value)
            return

        # Entry / その他
        try:
            widget.delete(0, tk.END)
            widget.insert(0, value)
        except Exception:
            pass

    # ========= ウィジェット作成 =========
    def _create_widgets(self):
        for i, label in enumerate(self.FIELD_LABELS):
            tk.Label(self, text=label).grid(row=i, column=0, padx=5, pady=5, sticky="e")

            if "日" in label:
                entry = NullableDateEntry(self, date_pattern="yyyy-mm-dd")
            elif label == "対応":
                entry = ttk.Combobox(self, values=list(self.types.values()), state="readonly")
            elif label == "状態":
                entry = ttk.Combobox(self, values=list(self.statuses.values()), state="readonly")
            elif label == "業者":
                entry = ttk.Combobox(self, values=list(self.vendors.values()), state="readonly")
            elif label in ("詳細", "備考"):
                entry = tk.Text(self, width=40, height=3)
            else:
                entry = tk.Entry(self)

            entry.grid(row=i, column=1, padx=5, pady=5, sticky="w")
            self.entries[label] = entry

        # --- PDF一覧表示フレームを右側に配置 ---
        self.pdf_frame = tk.LabelFrame(self, text="添付PDF一覧", padx=10, pady=10)
        self.pdf_frame.place(x=400, y=20, width=180, height=350)

        # PDF一覧表示（既存修理データがある場合）
        if self.repair_id:
            self._display_attached_pdfs()


        # ボタン
        tk.Button(self, text="保存", command=self.save_changes).grid(
            row=len(self.FIELD_LABELS), column=0, pady=10
        )
        tk.Button(self, text="PDF添付", command=self._attach_pdf).grid(
            row=len(self.FIELD_LABELS), column=1, pady=10, sticky="w"
        )

    def _display_attached_pdfs(self):
        """修理IDに紐づくPDF一覧を表示"""
        if not self.repair_id:
            return

        # 既存のPDF一覧をクリア
        for widget in self.pdf_frame.winfo_children():
            widget.destroy()

        pdf_dir = os.path.join("attached_pdfs", str(self.repair_id))
        if not os.path.exists(pdf_dir):
            return

        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]

        for i, name in enumerate(pdf_files):
            label = tk.Label(self.pdf_frame, text=name, fg="blue", cursor="hand2", anchor="w")
            label.grid(row=i, column=0, sticky="w")
            label.bind("<Button-1>", lambda e, file=os.path.join(pdf_dir, name): self._open_pdf(file))

    def _open_pdf(self, file_path):
        """PDFファイルを開く"""
        if not os.path.exists(file_path):
            messagebox.showerror("エラー", f"ファイルが存在しません:\n{file_path}")
            return
        try:
            if os.name == "nt":  # Windows
                os.startfile(file_path)
            elif os.name == "posix":
                subprocess.run(["xdg-open", file_path])
        except Exception as e:
            messagebox.showerror("エラー", f"PDFを開けませんでした:\n{e}")


    # ========= データ読み込み =========
    def load_repair_data(self, repair_id):
        """DBから修理情報を読み込みウィジェットに反映"""
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

    # ========= ID・名称変換 =========
    def get_name_from_id(self, id_value, key):
        mapping = {
            "状態": self.statuses,
            "対応": self.types,
            "業者": self.vendors
        }
        if key in mapping:
            return mapping[key].get(id_value, "")
        return id_value or ""

    def get_id_from_name(self, name, mapping):
        for id, nm in mapping.items():
            if nm == name:
                return id
        return None

    # ========= 保存処理 =========
    def save_changes(self):
        """修理情報の保存（新規 or 更新）"""
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
                            repairtype=?, vendor_id=?, technician=?, details=?, remarks=?
                        WHERE id=?
                    """, (
                        repairstatus_id, new_values["依頼日"], new_values["完了日"],
                        repairtype_id, vendor_id, new_values["技術者"],
                        new_values["詳細"], new_values["備考"], self.repair_id
                    ))
                else:  # 新規登録
                    cursor.execute("""
                        INSERT INTO repair
                        (equipment_code, repair_status_id, request_date, complete_date,
                         repairtype, vendor_id, technician, details, remarks)
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

    # ========= PDF添付 =========
    def _attach_pdf(parent=None):
        """PDFファイルを選択し、ファイル名を変更してpdf_docsに保存"""
        try:
            # PDF選択
            file_path = filedialog.askopenfilename(
                parent=parent,
                title="添付するPDFファイルを選択",
                filetypes=[("PDFファイル", "*.pdf")]
            )
            if not file_path:
                return  # キャンセル

            # 現在のファイル名（拡張子なし）
            base_name = os.path.splitext(os.path.basename(file_path))[0]

            # 保存ファイル名入力（デフォルトは現在のファイル名）
            new_name = simpledialog.askstring(
                "PDFファイル名を指定",
                "保存するファイル名を入力してください（拡張子 .pdf は自動で付きます）:",
                initialvalue=base_name,
                parent=parent
            )
            if not new_name:
                messagebox.showinfo("キャンセル", "PDF添付を中止しました。")
                return

            # 保存フォルダ作成
            save_dir = os.path.join(os.path.dirname(__file__), "pdf_docs")
            os.makedirs(save_dir, exist_ok=True)

            save_path = os.path.join(save_dir, f"{new_name}.pdf")

            # ファイルをコピー
            shutil.copy(file_path, save_path)

            messagebox.showinfo("完了", f"PDFを添付しました。\n保存先: {save_path}")

        except Exception as e:
            messagebox.showerror("エラー", f"PDF添付中にエラーが発生しました:\n{e}")
