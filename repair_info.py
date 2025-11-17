import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from contextlib import contextmanager
from typing import Dict, Any, Iterator
import os
import json

# 外部モジュール
from cls_master_data_fetcher import MasterDataFetcher
from edit_repair_window import EditRepairWindow


class RepairInfoWindow(tk.Toplevel):
    """
    器材情報と修理履歴を管理するウィンドウクラス。
    メインアプリから Toplevel として呼び出して利用します。
    """

    # JSON ファイルからデータベース名を取得
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    DB_NAME = config.get("db_name", "default.db")  # デフォルト値を設定
    

    FORM_CONFIG = [
        ("カテゴリ名", "categorie_name"), ("器材番号", "equipment_code"),
        ("器材名", "name"), ("状態", "status_name"), ("部門", "department_name"),
        ("部屋", "room_name"), ("製造元", "manufacturer_name"), ("販売元", "celler_name"),
        ("備考", "remarks"), ("購入日", "purchase_date"), ("モデル(シリアル)", "model")
    ]

    REPAIR_HISTORY_COLUMNS = {
        "status": {"text": "状態", "width": 80},
        "request_date": {"text": "依頼日", "width": 90},
        "completion_date": {"text": "完了日", "width": 90},
        "repair_type": {"text": "修理種別", "width": 90},
        "vendor": {"text": "業者", "width": 130},
        "technician": {"text": "技術者", "width": 100},
        "details": {"text": "詳細", "width": 300},  # 20251002 追加
        "remarks": {"text": "備考", "width": 200},  # 備考は一旦非表示
    }

    DEFAULT_MASTER_DATA = {
        "repair_type_master": [
            (1, "随意対応"), (2, "保守対応"), (3, "対応未定"), (4, "修理不能"), (5, "使用不能")
        ],
        "repair_statuse_master": [
            (1, "修理依頼中"), (2, "修理不能"), (3, "修理完了"), (4, "更新申請中"), (5, "廃棄")
        ]
    }

    def __init__(self, parent: tk.Widget, equipment_code:str):
        """
        Args:
            parent: 呼び出し元ウィンドウ (通常は root)
            equipment_code: 表示対象の器材ID
        """
        super().__init__(parent)
        self.equipment_db_id = None  # ← DBの主キー
        self.equipment_code = equipment_code              # ← 表示用の器材番号

        self.fetcher = MasterDataFetcher(self.DB_NAME)
        self.master_lookups = self._load_all_master_data_as_lookup()
        self.equipment_data: Dict[str, Any] = {}
        self.input_vars: Dict[str, tk.StringVar] = {}
        self.repair_tree: ttk.Treeview = None


        self.title("器材情報（参照）")
        self.geometry("1500x500")
        self.transient(parent)     # 親ウィンドウの手前に表示
        self.grab_set()            # モーダル表示    

        self._setup_ui()
        self._load_and_display_data()

    @contextmanager
    def _get_db_cursor(self) -> Iterator[sqlite3.Cursor]:
        conn = sqlite3.connect(self.DB_NAME)
        try:
            yield conn.cursor()
        finally:
            conn.close()

    def _load_all_master_data_as_lookup(self) -> Dict[str, Dict[int, str]]:
        tables = [
            "categorie_master", "statuse_master", "department_master", "room_master",
            "manufacturer_master", "celler_master",
            "repair_type_master", "repair_statuse_master",
        ]
        lookups = {}
        for table in tables:
            data = self.fetcher.fetch_all(table) or self.DEFAULT_MASTER_DATA.get(table, [])
            lookups[table] = {id: name for id, name in data}
        return lookups

    def _setup_ui(self):
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        form_frame = tk.Frame(main_frame)
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        repair_frame = tk.Frame(main_frame)
        repair_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._create_form_widgets(form_frame)
        self._create_repair_history_widgets(repair_frame)

    def _create_form_widgets(self, parent: tk.Frame):
        for i, (label, key) in enumerate(self.FORM_CONFIG):
            tk.Label(parent, text=label).grid(row=i, column=0, padx=5, pady=3, sticky="w")
            var = tk.StringVar()
            self.input_vars[key] = var
            tk.Entry(parent, textvariable=var, state="readonly", width=30).grid(
                row=i, column=1, padx=5, pady=3, sticky="we"
            )

        button_frame = tk.Frame(parent)
        button_frame.grid(row=len(self.FORM_CONFIG), column=0, columnspan=2, pady=20)
        tk.Button(button_frame, text="修理情報追加", command=self._open_add_repair).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="修理情報修正", command=self._open_edit_repair).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="閉じる", command=self.destroy).pack(side=tk.LEFT, padx=5)

    def _create_repair_history_widgets(self, parent: tk.Frame):
        columns_ids = list(self.REPAIR_HISTORY_COLUMNS.keys())
        self.repair_tree = ttk.Treeview(parent, columns=columns_ids, show='headings')

        for col_id in columns_ids:
            config = self.REPAIR_HISTORY_COLUMNS[col_id]
            self.repair_tree.heading(col_id, text=config["text"])
            self.repair_tree.column(col_id, width=config["width"], anchor="w", stretch=False)
            # デフォルトは左寄せ
            anchor = "center"
            # 完了日だけ中央寄せ
            if col_id in ("details", "remarks"):
                anchor = "w"

            self.repair_tree.column(
                col_id,
                width=config["width"],
                anchor=anchor,
                stretch=False
            )

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.repair_tree.yview)
        self.repair_tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.repair_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _load_and_display_data(self):
        with self._get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM equipment WHERE equipment_code = ?", (self.equipment_code,))
            data = cursor.fetchone()

        if not data:
            messagebox.showerror("データエラー", f"器材コード = {self.equipment_code} のデータが見つかりません。")
            self.destroy()
            return

        self.equipment_db_id = data[0]  # ← DB主キーを保持（修理追加用に必要）
        self.equipment_data = {
            "id": data[0],
            "equipment_code": data[1],  # 器材コード
            "name": data[2],
            "categorie_name": self.master_lookups["categorie_master"].get(data[4], "不明"),
            "status_name": self.master_lookups["statuse_master"].get(data[5], "不明"),
            "department_name": self.master_lookups["department_master"].get(data[6], "不明"),
            "room_name": self.master_lookups["room_master"].get(data[7], "不明"),
            "manufacturer_name": self.master_lookups["manufacturer_master"].get(data[8], "不明"),
            "celler_name": self.master_lookups["celler_master"].get(data[9], "不明"),
            "remarks": data[10],
            "purchase_date": data[11],
            "model": data[12]
        }

        self._update_form()
        self.refresh_repair_history()


    def _update_form(self):
        for key, var in self.input_vars.items():
            var.set(self.equipment_data.get(key, ""))

    def refresh_repair_history(self):
        for item in self.repair_tree.get_children():
            self.repair_tree.delete(item)

        query = """
            SELECT r.id,
                rs.name AS status, 
                r.request_date,
                r.completion_date,
                rt.name AS repair_type,
                c.name AS vendor,
                r.technician,
                r.details,
                r.remarks
            FROM repair r
            LEFT JOIN repair_statuse_master rs ON r.repairstatuses = rs.id
            LEFT JOIN repair_type_master rt ON r.repairtype = rt.id
            LEFT JOIN celler_master c ON r.vendor = c.id
            WHERE r.equipment_code = ?
            ORDER BY r.request_date DESC;
        """
        with self._get_db_cursor() as cursor:
            cursor.execute(query, (self.equipment_code,),)
            repairs = cursor.fetchall()

        for row in repairs:
            # row[0] = id, 以降を TreeView に渡す
            self.repair_tree.insert("", tk.END, iid=str(row[0]), values=row[1:])


    def _open_add_repair(self):
        try:
            if not getattr(self, "equipment_code", None):
                messagebox.showwarning("注意", "器材が選択されていません。")
                return

            EditRepairWindow(
                parent=self,
                db_name=self.DB_NAME,
                equipment_code=self.equipment_code,
                repair_id=None,
                refresh_callback=self.refresh_repair_history
            )
        except Exception as e:
            messagebox.showerror("例外発生", f"修理情報追加中にエラーが発生しました:\n{e}")


    def _open_edit_repair(self):
        selected_ids = self.repair_tree.selection()
        if not selected_ids:
            messagebox.showwarning("選択なし", "修正する修理情報を選択してください。")
            return

        repair_id = int(selected_ids[0])
        try:
            EditRepairWindow(
                parent=self,
                db_name=self.DB_NAME,
                equipment_code=self.equipment_code,
                repair_id=repair_id,                
                refresh_callback=self.refresh_repair_history
            )
        except Exception as e:
            messagebox.showerror("例外発生", f"修理情報修正中にエラーが発生しました:\n{e}")
