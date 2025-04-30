import tkinter as tk
from tkinter import ttk

def create_equipment_treeview(parent):
    columns = ("カテゴリ", "機器コード", "機器名", "状態", "部門", "部屋", "製造元", "販売元", "備考", "購入日", "型番")
    tree = ttk.Treeview(parent, columns=columns, show="headings")
    
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=100)

    return tree
