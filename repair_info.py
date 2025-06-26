import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from contextlib import contextmanager
from typing import Dict, Any, List, Tuple, Iterator

# 外部モジュールのインポート
from cls_master_data_fetcher import MasterDataFetcher
from cls_edit_repair_window import EditRepairWindow

class RepairInfoWindow:
    """
    器材情報と修理履歴を管理する高効率・高メンテナンス性ウィンドウクラス。

    定数の一元化、DB接続のコンテキスト管理、マスタデータの事前キャッシュにより、
    コードの可読性、保守性、パフォーマンスを向上させています。
    """
    # --- 定数の一元管理 ---
    DB_NAME = "equipment_management.db"

    # フォームの構成情報 (ラベルテキスト, データ辞書のキー)
    FORM_CONFIG = [
        ("カテゴリ名", "category_name"), ("器材番号", "equipment_id"),
        ("器材名", "name"), ("状態", "status_name"), ("部門", "department_name"),
        ("部屋", "room_name"), ("製造元", "manufacturer_name"), ("販売元", "celler_name"),
        ("備考", "remarks"), ("購入日", "purchase_date"), ("モデル(シリアル)", "model")
    ]

    # 修理履歴Treeviewの構成情報 (内部名: {表示テキスト, 幅})
    REPAIR_HISTORY_COLUMNS = {
        "status": {"text": "状態", "width": 100},
        "request_date": {"text": "依頼日", "width": 120},
        "completion_date": {"text": "完了日", "width": 120},
        "repair_type": {"text": "修理種別", "width": 100},
        "vendor": {"text": "業者", "width": 120},
        "technician": {"text": "技術者", "width": 100}
    }

    # マスタデータが空だった場合のデフォルト値
    DEFAULT_MASTER_DATA = {
        "repair_type_master": [(1, "随意対応"), (2, "保守対応"), (3, "対応未定"), (4, "修理不能"), (5, "使用不能")],
        "repair_status_master": [(1, "修理依頼中"), (2, "修理不能"), (3, "修理完了"), (4, "更新申請中"), (5, "廃棄")]
    }

    def __init__(self, equipment_id: str):
        """
        ウィンドウを初期化し、UIとデータをセットアップします。
        Args:
            equipment_id (str): 表示する器材のID。
        """
        self.root = tk.Tk()
        self.root.title("器材情報（参照）")

        self.equipment_id = equipment_id
        self.fetcher = MasterDataFetcher(self.DB_NAME)
        
        # --- パフォーマンス向上のためのデータキャッシュ ---
        self.master_lookups = self._load_all_master_data_as_lookup()
        
        self.equipment_data: Dict[str, Any] = {}
        self.input_vars: Dict[str, tk.StringVar] = {}
        self.repair_tree: ttk.Treeview = None
        
        self._setup_ui()
        self._load_and_display_data()

    @contextmanager
    def _get_db_cursor(self) -> Iterator[sqlite3.Cursor]:
        """データベース接続を管理するコンテキストマネージャ。"""
        conn = sqlite3.connect(self.DB_NAME)
        try:
            yield conn.cursor()
        finally:
            conn.close()

    def _load_all_master_data_as_lookup(self) -> Dict[str, Dict[int, str]]:
        """
        全てのマスタデータを読み込み、ID->名称の辞書（ルックアップテーブル）としてキャッシュする。
        これにより、名称検索時のDBアクセスが不要になり、パフォーマンスが向上します。
        """
        master_tables = [
            "category_master", "status_master", "department_master", "room_master",
            "manufacturer_master", "celler_master", "repair_category_master", "repair_status_master", "repair_type_master"
        ]
        lookups = {}
        for table in master_tables:
            data = self.fetcher.fetch_all(table) or self.DEFAULT_MASTER_DATA.get(table, [])
            lookups[table] = {id: name for id, name in data}
        return lookups

    def _setup_ui(self):
        """ウィンドウのUIウィジェットをセットアップします。"""
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        form_frame = tk.Frame(main_frame)
        form_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        repair_frame = tk.Frame(main_frame)
        repair_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._create_form_widgets(form_frame)
        self._create_repair_history_widgets(repair_frame)

    def _create_form_widgets(self, parent: tk.Frame):
        """設定（FORM_CONFIG）に基づき、情報表示フォームを作成します。"""
        for i, (label, key) in enumerate(self.FORM_CONFIG):
            tk.Label(parent, text=label).grid(row=i, column=0, padx=5, pady=3, sticky="w")
            var = tk.StringVar()
            self.input_vars[key] = var
            tk.Entry(parent, textvariable=var, state="readonly", width=30).grid(row=i, column=1, padx=5, pady=3, sticky="we")

        button_frame = tk.Frame(parent)
        button_frame.grid(row=len(self.FORM_CONFIG), column=0, columnspan=2, pady=20)
        tk.Button(button_frame, text="修理情報追加", command=self._open_add_repair).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="修理情報修正", command=self._open_edit_repair).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="戻る", command=self.root.destroy).pack(side=tk.LEFT, padx=5)

    def _create_repair_history_widgets(self, parent: tk.Frame):
        """設定（REPAIR_HISTORY_COLUMNS）に基づき、修理履歴Treeviewを作成します。"""
        columns_ids = list(self.REPAIR_HISTORY_COLUMNS.keys())
        self.repair_tree = ttk.Treeview(parent, columns=columns_ids, show='headings')
        
        for col_id in columns_ids:
            config = self.REPAIR_HISTORY_COLUMNS[col_id]
            self.repair_tree.heading(col_id, text=config["text"])
            self.repair_tree.column(col_id, width=config["width"], anchor='center')
        
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.repair_tree.yview)
        self.repair_tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.repair_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _load_and_display_data(self):
        """データベースから器材情報を取得し、UIに表示します。"""
        with self._get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM equipment WHERE equipment_id = ?", (self.equipment_id,))
            data = cursor.fetchone()

        if not data:
            messagebox.showerror("データエラー", f"器材ID = {self.equipment_id} のデータが見つかりません。")
            self.root.destroy()
            return

        self.equipment_data = {
            "id": data[0], "equipment_id": data[1], "name": data[2],
            "category_name": self.master_lookups["category_master"].get(data[4], "不明"),
            "status_name": self.master_lookups["status_master"].get(data[5], "不明"),
            "department_name": self.master_lookups["department_master"].get(data[6], "不明"),
            "room_name": self.master_lookups["room_master"].get(data[7], "不明"),
            "manufacturer_name": self.master_lookups["manufacturer_master"].get(data[8], "不明"),
            "celler_name": self.master_lookups["celler_master"].get(data[9], "不明"),
            "remarks": data[10], "purchase_date": data[11], "model": data[12]
        }
        
        self._update_form()
        self.refresh_repair_history()

    def _update_form(self):
        """フォームの各入力欄に最新の器材情報を表示します。"""
        for key, var in self.input_vars.items():
            var.set(self.equipment_data.get(key, ""))

    def refresh_repair_history(self):
        """修理履歴をデータベースから再取得し、Treeviewを更新します。"""
        for item in self.repair_tree.get_children():
            self.repair_tree.delete(item)
        
        query = """
            SELECT r.id, rs.name, r.request_date, r.completion_date,
                   rc.name, c.name, r.technician
            FROM repair r
            LEFT JOIN repair_status_master rs ON r.repairstatuses = rs.id
            LEFT JOIN repair_type_master rc ON r.repairtype = rc.id
            LEFT JOIN celler_master c ON r.vendor = c.id
            WHERE r.equipment_id = ? ORDER BY r.request_date DESC;
        """
        with self._get_db_cursor() as cursor:
            cursor.execute(query, (self.equipment_data['equipment_id'],))
            repairs = cursor.fetchall()

        for row in repairs:
            self.repair_tree.insert('', tk.END, iid=row[0], values=row[1:])

    def _open_add_repair(self):
        """修理情報追加ウィンドウを開きます（プレースホルダ）。"""
        messagebox.showinfo("修理情報追加", "修理情報追加画面を開く処理をここに実装します。")

    def _open_edit_repair(self):
        """選択された修理情報を修正するウィンドウを開きます。"""
        selected_ids = self.repair_tree.selection()
        if not selected_ids:
            messagebox.showwarning("選択なし", "修正する修理情報を選択してください。")
            return
        
        repair_id = selected_ids[0]
        try:
           EditRepairWindow(
                parent=self.root, db_name=self.DB_NAME, repair_id=repair_id,
                refresh_callback=self.refresh_repair_history
            )
        except Exception as e:
            messagebox.showerror("例外発生", f"編集ウィンドウの表示中にエラーが発生しました:\n{e}")

    def run(self):
        """メインループを開始し、ウィンドウを表示します。"""
        self.root.mainloop()

def main():
    """アプリケーションのエントリーポイント。"""
    if len(sys.argv) > 1:
        equipment_id = sys.argv[1]
        print("DEBUG: equipment_id =", equipment_id)  # ← 追加
        app = RepairInfoWindow(equipment_id=equipment_id)
        app.run()
    else:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("引数エラー", "器材IDが指定されていません。")
        print(f"使用法: python {sys.argv[0]} <equipment_id>")
        sys.exit(1)

if __name__ == "__main__":
    main()