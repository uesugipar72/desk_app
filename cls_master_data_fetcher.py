import sqlite3
class MasterDataFetcher:
    """
    マスターテーブルからデータを取得するクラス。
    """
    def __init__(self, db_name):
        self.db_name = db_name  # 使用するデータベース名

    def fetch_all(self, table_name):
        """
        指定したテーブルからすべてのデータを取得。
        :param table_name: データを取得するテーブル名
        :return: [(id, name), ...] の形式のリスト
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(f"SELECT id, name FROM {table_name}")
            data = cursor.fetchall()  # [(id1, name1), (id2, name2), ...]
            conn.close()
            return data
        except Exception as e:
            print(f"エラー: {e}")
            return []

    def fetch_name_by_id(self, table_name, record_id):
        """
        指定したIDに対応する名前を取得。
        :param table_name: 検索するテーブル名
        :param record_id: 検索するレコードID
        :return: 対応する名前、見つからなければ None
        """
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(f"SELECT name FROM {table_name} WHERE id = ?", (record_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            print(f"エラー: {e}")
            return None
