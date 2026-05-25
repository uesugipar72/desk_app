import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkFont

# 作成したModel層から必要なクラスをインポート
from models.master_model import MasterModel
from models.repair_model import RepairModel

# ※修理情報を登録・編集する画面（別ウィンドウ）を同じviewsフォルダからインポートする想定
# (既存のファイルを再利用する場合は、配置パスに合わせて書き換えてください)
# from views.edit_repair_window import EditRepairWindow


class RepairInfoWindow(tk.Toplevel):
    """
    特定の機器に紐づく詳細情報と、これまでの修理履歴一覧を表示・管理する画面。
    メイン画面から Toplevel (サブウィンドウ) として呼び出されます。
    """

    # 上部エリアに表示する機器情報の項目定義 (画面のラベル名, 辞書のキー名)
    FORM_CONFIG = [
        ("機器分類", "categorie_name"), ("器材番号", "equipment_code"),
        ("機器名", "name"), ("状態", "status_name"), ("部門", "department_name"),
        ("部屋", "room_name"), ("製造元", "manufacturer_name"), ("販売元", "celler_name"),
        ("備考", "remarks"), ("購入日", "purchase_date"), ("モデル(シリアル)", "model")
    ]

    def __init__(self, parent, equipment_code: str):
        super().__init__(parent)
        self.parent = parent
        self.equipment_code = equipment_code

        self.title(f"修理履歴管理 - 器材番号: {self.equipment_code}")
        self.geometry("1000x650")
        
        # モーダルウィンドウ（この画面を閉じるまでメイン画面を操作できない）にする設定
        self.grab_set()

        self._create_widgets()
        
        # データを読み込んで画面に反映
        self.load_equipment_detail()
        self.refresh_repair_history()

    def _create_widgets(self):
        """画面ウィジェットの配置"""
        # 1. 機器の基本情報表示エリア (上部)
        frame_info = ttk.LabelFrame(self, text="機器基本情報", padding=10)
        frame_info.pack(fill="x", padx=10, pady=5)

        self.info_labels = {}
        for i, (label_text, key) in enumerate(self.FORM_CONFIG):
            row = i // 4
            col = (i % 4) * 2
            
            lbl_title = ttk.Label(frame_info, text=f"{label_text}:", font=("Helvetica", 9, "bold"))
            lbl_title.grid(row=row, column=col, padx=5, pady=5, sticky="e")
            
            # 値を表示するためのラベル (読み取り専用)
            lbl_value = ttk.Label(frame_info, text="", background="#f0f0f0", width=20, anchor="w", padding=2)
            lbl_value.grid(row=row, column=col+1, padx=5, pady=5, sticky="w")
            self.info_labels[key] = lbl_value

        # 2. 修理履歴一覧エリア (下部)
        frame_history = ttk.LabelFrame(self, text="修理・保守履歴", padding=10)
        frame_history.pack(fill="both", expand=True, padx=10, pady=5)

        # 履歴操作用ボタン
        frame_btns = ttk.Frame(frame_history)
        frame_btns.pack(fill="x", pady=5)

        btn_add = ttk.Button(frame_btns, text="修理履歴の追加", command=self._open_add_repair)
        btn_add.pack(side="left", padx=5)

        btn_edit = ttk.Button(frame_btns, text="選択した履歴の修正", command=self._open_edit_repair)
        btn_edit.pack(side="left", padx=5)

        btn_refresh = ttk.Button(frame_btns, text="履歴の更新", command=self.refresh_repair_history)
        btn_refresh.pack(side="right", padx=5)

        # Treeview（履歴の一覧表）
        columns = ("status", "req_date", "comp_date", "type", "vendor", "technician", "details", "remarks")
        self.repair_tree = ttk.Treeview(frame_history, columns=columns, show="headings")
        
        # 列ヘッダーの定義
        headers = {
            "status": "修理状態", "req_date": "依頼日", "comp_date": "完了日",
            "type": "修理種別", "vendor": "業者名", "technician": "対応技術者",
            "details": "修理詳細内容", "remarks": "備考"
        }
        for col, text in headers.items():
            self.repair_tree.heading(col, text=text)
            self.repair_tree.column(col, width=110, anchor="w" if col in ["details", "remarks"] else "center")

        # スクロールバー
        vsb = ttk.Scrollbar(frame_history, orient="vertical", command=self.repair_tree.yview)
        hsb = ttk.Scrollbar(frame_history, orient="horizontal", command=self.repair_tree.xview)
        self.repair_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.repair_tree.pack(side="top", fill="both", expand=True)
        vsb.pack(side="right", fill="y", before=self.repair_tree)
        hsb.pack(side="bottom", fill="x")

    def load_equipment_detail(self):
        """Modelから機器の最新詳細情報を取得し、画面上部のラベルにセットする"""
        # SQLを使わず、辞書形式で整形されたデータを1行で取得
        detail = RepairModel.get_equipment_detail_by_code(self.equipment_code)
        
        if not detail:
            messagebox.showerror("エラー", "指定された機器の情報が見つかりませんでした。")
            self.destroy()
            return

        # ラベルに値を反映
        for key, label_widget in self.info_labels.items():
            val = detail.get(key, "")
            label_widget.config(text=str(val) if val is not None else "")

    def refresh_repair_history(self):
        """Modelから修理履歴を取得し、Treeviewの表示を最新にする"""
        # Treeviewの既存データをクリア
        for item in self.repair_tree.get_children():
            self.repair_tree.delete(item)

        # Modelからマスタ名がLEFT JOIN結合済みの綺麗なレコードリストを取得
        repairs = RepairModel.get_history_by_equipment(self.equipment_code)

        for row in repairs:
            # row: (id, status, request_date, completion_date, repair_type, vendor, technician, details, remarks)
            # row[0] はレコードのID（非表示）、row[1:] が画面に渡すデータ
            repair_id = row[0]
            self.repair_tree.insert("", tk.END, iid=str(repair_id), values=row[1:])

    def _open_add_repair(self):
        """新規修理履歴の追加ウィンドウを開く"""
        try:
            # TODO: 今後 views/edit_repair_window.py を作成した際に連携させます
            messagebox.showinfo("開発中", f"器材【{self.equipment_code}】の新規修理登録画面を開きます（次のステップで実装）")
            
            # 実装後の呼び出しイメージ:
            # EditRepairWindow(parent=self, equipment_code=self.equipment_code, repair_id=None, callback=self.refresh_repair_history)
        except Exception as e:
            messagebox.showerror("例外発生", f"修理情報追加画面の起動中にエラーが発生しました:\n{e}")

    def _open_edit_repair(self):
        """選択された既存履歴の修正ウィンドウを開く"""
        selected_ids = self.repair_tree.selection()
        if not selected_ids:
            messagebox.showwarning("選択なし", "修正する修理情報を選択してください。")
            return

        # Treeviewの iid に設定しておいた DBの repair_id を取得
        repair_id = int(selected_ids[0])
        
        try:
            # TODO: 今後 views/edit_repair_window.py を作成した際に連携させます
            messagebox.showinfo("開発中", f"修理履歴ID【{repair_id}】の編集画面を開きます（次のステップで実装）")
            
            # 実装後の呼び出しイメージ:
            # EditRepairWindow(parent=self, equipment_code=self.equipment_code, repair_id=repair_id, callback=self.refresh_repair_history)
        except Exception as e:
            messagebox.showerror("例外発生", f"修理情報修正画面の起動中にエラーが発生しました:\n{e}")