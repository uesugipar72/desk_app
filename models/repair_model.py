from typing import List, Tuple, Any, Optional, Dict
from .db_manager import DBManager

class RepairModel:
    """
    修理履歴（repair）テーブルおよび、修理履歴画面に関連する
    データベース操作（SQL実行）を管理するモデルクラス。
    実際のDB構造（テーブル名・カラム名）に完全に対応しています。
    """

    @staticmethod
    def get_equipment_detail_by_code(equipment_code: str) -> Optional[Dict[str, Any]]:
        """
        機器コードをキーに、修理画面の上部表示に必要な機器の情報をマスタ名と結合して1件取得します。
        """
        query = """
            SELECT 
                e.equipment_code,
                e.name,
                e.model,
                c.name AS category_name,
                s.name AS status_name,
                d.name AS department_name,
                r.name AS room_name,
                m.name AS manufacturer_name,
                v.name AS celler_name,
                e.remarks,
                e.purchase_date
            FROM equipment e
            LEFT JOIN categorie_master c ON e.categorie_id = c.id
            LEFT JOIN statuse_master s ON e.statuse_id = s.id
            LEFT JOIN department_master d ON e.department_id = d.id
            LEFT JOIN room_master r ON e.room_id = r.id
            LEFT JOIN manufacturer_master m ON e.manufacturer_id = m.id
            LEFT JOIN celler_master v ON e.celler_id = v.id
            WHERE e.equipment_code = ?
        """
        try:
            with DBManager.get_cursor() as cursor:
                cursor.execute(query, (equipment_code,))
                row = cursor.fetchone()
                
            if row:
                return {
                    "equipment_code": row[0],
                    "name": row[1],
                    "model": row[2],
                    "categorie_name": row[3],
                    "status_name": row[4],
                    "department_name": row[5],
                    "room_name": row[6],
                    "manufacturer_name": row[7],
                    "celler_name": row[8],
                    "remarks": row[9],
                    "purchase_date": row[10]
                }
            return None
        except Exception as e:
            print(f"[-] 修理画面用機器情報取得エラー: {e}")
            return None

    @staticmethod
    def get_history_by_equipment(equipment_code: str) -> List[Tuple[Any, ...]]:
        """
        指定された機器コードに紐づく修理履歴の一覧を、マスタ文字列を結合した状態で取得します。
        ※ repair_status_master, repair_type_master へのJOINを正確に修正しました。
        """
        query = """
            SELECT 
                r.id,
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
            ORDER BY r.request_date DESC, r.id DESC;
        """
        try:
            with DBManager.get_cursor() as cursor:
                cursor.execute(query, (equipment_code,))
                return cursor.fetchall()
        except Exception as e:
            print(f"[-] 修理履歴一覧取得エラー: {e}")
            return []

    @staticmethod
    def get_repair_record_by_id(repair_id: int) -> Optional[Tuple[Any, ...]]:
        """
        修理IDをキーに、特定の修理レコードを1件生のデータ（マスタIDのまま）で取得します。
        編集画面を開いたときに、コンボボックスに値を再セットするために使用します。
        """
        query = """
            SELECT 
                id, equipment_code, repairstatuses, request_date, 
                completion_date, repairtype, vendor, technician, details, remarks
            FROM repair
            WHERE id = ?
        """
        try:
            with DBManager.get_cursor() as cursor:
                cursor.execute(query, (repair_id,))
                return cursor.fetchone()
        except Exception as e:
            print(f"[-] 修理レコード単一取得エラー (ID: {repair_id}): {e}")
            return None

    @staticmethod
    def add_repair_record(data: dict) -> bool:
        """新しい修理履歴を追加します"""
        query = """
            INSERT INTO repair (
                equipment_code, repairstatuses, request_date, 
                completion_date, repairtype, vendor, technician, details, remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            data.get("equipment_code"),
            data.get("repairstatuses"),
            data.get("request_date"),
            data.get("completion_date"),
            data.get("repairtype"),
            data.get("vendor"),
            data.get("technician"),
            data.get("details"),
            data.get("remarks")
        )
        try:
            with DBManager.get_cursor() as cursor:
                cursor.execute(query, params)
            return True
        except Exception as e:
            print(f"[-] 修理情報追加エラー: {e}")
            return False

    @staticmethod
    def update_repair_record(repair_id: int, data: dict) -> bool:
        """既存の修理履歴を更新（修正）します"""
        query = """
            UPDATE repair SET
                repairstatuses = ?,
                request_date = ?,
                completion_date = ?,
                repairtype = ?,
                vendor = ?,
                technician = ?,
                details = ?,
                remarks = ?
            WHERE id = ?
        """
        params = (
            data.get("repairstatuses"),
            data.get("request_date"),
            data.get("completion_date"),
            data.get("repairtype"),
            data.get("vendor"),
            data.get("technician"),
            data.get("details"),
            data.get("remarks"),
            repair_id
        )
        try:
            with DBManager.get_cursor() as cursor:
                cursor.execute(query, params)
            return True
        except Exception as e:
            print(f"[-] 修理情報更新エラー (ID: {repair_id}): {e}")
            return False