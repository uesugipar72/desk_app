import sqlite3
import tkinter as tk
from tkinter import ttk

def fetch_data(equipment_id=None, name=None, name_kana=None, categorie_id=None, statuse_id=None, department_id=None ,room_id=None, manufacturer_id=None, celler_id=None, remarks=None):
    """
    検索条件に基づいてデータを抽出
    """
    with sqlite3.connect("equipment_management.db") as conn:
        cursor = conn.cursor()
        
        # 検索条件のリストとパラメータリストを準備
        query = """
            SELECT id, equipment_id, name, name_kana, categorie_id, statuse_id, department_id, room_id, manufacturer_id, celler_id, remarks, purchase_date, model
            FROM equipment
            WHERE 1=1
        """
        params = []
        
        if equipment_id:
            query += " AND equipment_id LIKE ?"
            params.append(f"%{equipment_id}%")  # 部分一致検索
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        
        if name_kana:
            query += " AND name_kana LIKE ?"
            params.append(f"%{name_kana}%")

        if categorie_id:
            query += " AND categorie_id = ?"
            params.append(categorie_id) 
        
        if statuse_id:
            query += " AND statuse_id = ?"
            params.append(statuse_id)
        
        if department_id:
            query += " AND department_id = ?"
            params.append(department_id)

        if room_id:
            query += " AND room_id = ?"
            params.append(room_id)        
        
        if manufacturer_id:
            query += " AND manufacturer_id = ?"
            params.append(manufacturer_id)

        if celler_id:
            query += " AND celler_id = ?"
            params.append(celler_id)

        if remarks:
            query += " AND remarks LIKE ?"
            params.append(f"%{remarks}%")
        
        
        # クエリ実行
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return rows
        # conn.close() withにより不要
