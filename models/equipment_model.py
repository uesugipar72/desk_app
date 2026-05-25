from typing import List, Tuple, Any, Optional
from .db_manager import DBManager

class EquipmentModel:
    """機器（Equipment）テーブルに関するデータ操作を管理するモデル"""

    @staticmethod
    def search_equipments(
        equipment_code: Optional[str] = None,
        name: Optional[str] = None,
        name_kana: Optional[str] = None,
        category_id: Optional[int] = None,
        statuse_id: Optional[int] = None,
        department_id: Optional[int] = None,
        room_id: Optional[int] = None,
        manufacturer_id: Optional[int] = None,
        celler_id: Optional[int] = None,
        remarks: Optional[str] = None
    ) -> List[Tuple[Any, ...]]:
        """
        指定された条件で機器情報を検索し、レコードのリストを返します。
        (※従来の equipment_search.py の fetch_data に相当する処理)
        """
        query = "SELECT * FROM equipment WHERE 1=1"
        params = []

        if equipment_code:
            query += " AND equipment_code LIKE ?"
            params.append(f"%{equipment_code}%")
        if name:
            query += " AND name LIKE ?"
            params.append(f"%{name}%")
        if name_kana:
            query += " AND name_kana LIKE ?"
            params.append(f"%{name_kana}%")
        if category_id:
            query += " AND categorie_id = ?"
            params.append(category_id)
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

        with DBManager.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchall()

    @staticmethod
    def get_by_code(equipment_code: str) -> Optional[Tuple[Any, ...]]:
        """器材コードをキーに、単一の機器情報を取得します（修理画面用）"""
        query = "SELECT * FROM equipment WHERE equipment_code = ?"
        with DBManager.get_cursor() as cursor:
            cursor.execute(query, (equipment_code,))
            return cursor.fetchone()