import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

db_name = "equipment_management.db"

def open_master_list_window(parent,table_name):
    master_win = tk.Toplevel(parent)
    master_win.title(f"{table_name} List")
    master_win.geometry("500x300")

     # columnsを先に取得
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    conn.close()

    tree = ttk.Treeview(master_win, columns=columns, show='headings')
    tree.pack(expand=True, fill='both')

    def refresh_treeview():
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        records = cursor.fetchall()
        conn.close()
        
        tree.delete(*tree.get_children())  # 既存データをクリア
        for record in records:
            tree.insert("", "end", values=record)

    # ヘッダの再設定(初回のみ設定するためインデントを一つ前に)
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=100)

    refresh_treeview()
    
    def on_double_click(event):
        item = tree.selection()[0]
        values = tree.item(item, "values")
        open_update_window(master_win,table_name, values)
    
    tree.bind("<Double-1>", on_double_click)
    
    # ボタン用フレームを作成（横並びのため）
    button_frame = tk.Frame(master_win)
    button_frame.pack(pady=10)

    # 「New Entry」ボタン
    tk.Button(button_frame, text="New Entry", command=lambda: open_update_window(master_win, table_name, None)).grid(row=0, column=0, padx=5)
    # 「Cancel」ボタン
    tk.Button(button_frame, text="Cancel", command=master_win.destroy).grid(row=0, column=1, padx=5)

def open_update_window(parent, table_name, record=None):
    update_win = tk.Toplevel(parent)    
    update_win.title(f"Update {table_name}")
    update_win.geometry("400x300")
    
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [col[1] for col in cursor.fetchall()]
    conn.close()
    
    entries = {}
    for i, col in enumerate(columns):
        tk.Label(update_win, text=col).grid(row=i, column=0, padx=5, pady=5)
        entry = tk.Entry(update_win)
        entry.grid(row=i, column=1, padx=5, pady=5)
        entries[col] = entry
    
    if record:
        for col, value in zip(columns, record):
            entries[col].insert(0, value)
    else:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"SELECT MAX(id) FROM {table_name}")
        max_id = cursor.fetchone()[0] or 0
        conn.close()
        entries['id'].insert(0, max_id + 1)
    
    def update_table():
        values = [entry.get() for entry in entries.values()]
        if any(v == "" for v in values):
            messagebox.showwarning("Warning", "All fields must be filled!")
            return
        
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        if record:
            set_clause = ', '.join([f"{col} = ?" for col in columns])
            cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE id = ?", values + [record[0]])
        else:
            placeholders = ', '.join(['?'] * len(columns))
            cursor.execute(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})", values)
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "Record updated successfully!")
        update_win.destroy()

    tk.Button(update_win, text="Save", command=update_table).grid(row=len(columns), column=0, columnspan=2, pady=10)
    # Cancelボタン
    tk.Button(update_win, text="Cancel", command=update_win.destroy).grid(row=len(columns), column=1, pady=10)



    
