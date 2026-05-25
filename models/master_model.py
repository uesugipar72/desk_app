from typing import List, Tuple, Dict, Optional
from .db_manager import DBManager

class MasterModel:
    """
    マスタテーブルからデータを取得・加工するモデルクラス。
    旧 MasterDataFetcher の機能を拡張し、MVCパターンに対応させています。
    """

    # 万が一データベースからデータが取得できなかった場合のデフォルト値（バックアップ）
    DEFAULT_MASTER_DATA: Dict[str, List[Tuple[int, str]]] = {
        "categorie_master": [(1, "検査機器"), (2, "一般備品"), (3, "消耗品"), (4, "その他")],
        "statuse_master": [(1, "使用中"), (2, "良好"), (3, "修理中"), (4, "廃棄")],
        "department_master": [(1, "検査科"), (2, "検体検査"), (3, "生理検査"), (4, "細菌検査"), (5, "病理検査"), (6, "採血室")],
        "room_master": [(1, "受付_染色室"), (2, "鏡検室"), (3, "臓器固定・切出室"), (4, "標本作製室"), (5, "病理標本保存室"), (6, "病理診断室"), (8, "剖検室"), (9, "剖検前室")],
        "repair_type_master": [(1, "随意対応"), (2, "保守対応"), (3, "対応未定"), (4, "修理不能"), (5, "使用不能")],
        "repair_statuse_master": [(1, "修理依頼中"), (2, "修理不能"), (3, "修理完了"), (4, "更新申請中"), (5, "廃棄")]
    }

    @classmethod
    def fetch_all(cls, table_name: str) -> List[Tuple[int, str]]:
        """
        指定したマスタテーブルからすべての (id, name) リストを取得します。
        DB接続エラーやテーブルが空の場合は、デフォルトのデータを返します。
        """
        query = f"SELECT id, name FROM {table_name}"
        try:
            with DBManager.get_cursor() as cursor:
                cursor.execute(query)
                data = cursor.fetchall()
                
            # データが取得できればそれを返し、空ならデフォルト値をチェック
            if data:
                return data
            return cls.DEFAULT_MASTER_DATA.get(table_name, [])
            
        except Exception as e:
            print(f"[-] マスタデータ取得エラー ({table_name}): {e}")
            # エラー発生時もシステムがクラッシュしないようデフォルト値を返す
            return cls.DEFAULT_MASTER_DATA.get(table_name, [])

    @classmethod
    def get_kv_lookup(cls, table_name: str) -> Dict[int, str]:
        """
        画面表示（IDから名称への変換）で頻出する {id: name} の辞書形式に変換して取得します。
        
        使用例:
            lookups = MasterModel.get_kv_lookup("categorie_master")
            cat_name = lookups.get(1, "不明")  # -> "検査機器" が取得できる
        """
        data = cls.fetch_all(table_name)
        return {row[0]: row[1] for row in data}

    @staticmethod
    def fetch_name_by_id(table_name: str, record_id: int) -> Optional[str]:
        """
        指定したIDに対応する名前をピンポイントで1件取得します（旧メソッドの維持）。
        """
        query = f"SELECT name FROM {table_name} WHERE id = ?"
        try:
            with DBManager.get_cursor() as cursor:
                cursor.execute(query, (record_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"[-] マスタ個別取得エラー ({table_name}, ID: {record_id}): {e}")
            return None