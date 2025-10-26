import sqlite3

class EquipmentManager:
    used_codes_per_field = {}  # 分野ごとに使用済み機器コードを管理

    def __init__(self, field_code: int):
        self.field_code = field_code  # 整数
        if not (1 <= field_code <= 10):
            raise ValueError("分野コードは 01～10 の範囲で指定してください。")  
        # self.field_code = f"{field_code:02d}"

        # 指定した分野の使用済みコードリストがなければ作成
        if self.field_code not in EquipmentManager.used_codes_per_field:
            EquipmentManager.used_codes_per_field[self.field_code] = self._fetch_used_codes()

        print(f"[DEBUG] 初期化: {self.field_code}, 既存コード: {EquipmentManager.used_codes_per_field[self.field_code]}")

    def _fetch_used_codes(self):
        """ DBから使用済みのequipment_codeを取得 """
        used_codes = set()
        try:
            conn = sqlite3.connect("equipment_management.db")
            cursor = conn.cursor()
            query = """
                SELECT equipment_code FROM equipment
                WHERE equipment_code = ?
            """
            cursor.execute(query, (self.field_code,))
            rows = cursor.fetchall()
            used_codes = {row[0] for row in rows}
        except sqlite3.Error as e:
            print(f"[ERROR] データベースエラー: {e}")
        finally:
            conn.close()
        
        return used_codes

    def generate_equipment_number(self) -> str:
        """ 器材番号を自動生成（5桁: 分野コード + 固有機器コード） """
        used_codes = EquipmentManager.used_codes_per_field[self.field_code]

        for code in range(1, 1000):  # 001～999
            equipment_code = f"{code:03d}"
            equipment_number = self.field_code + equipment_code

            if equipment_number not in used_codes:
                EquipmentManager.used_codes_per_field[self.field_code].add(equipment_number)  # クラス変数に追加
                print(f"[DEBUG] 生成成功: {equipment_number}")
                return equipment_number

        raise Exception(f"分野 {self.field_code} の機器コードがすべて使用されています。")
# テスト
# manager1 = EquipmentManager(1)
# print(manager1.generate_equipment_number())  # 01001
# print(manager1.generate_equipment_number())  # 01002

# manager2 = EquipmentManager(1)
# print(manager2.generate_equipment_number())  # 01003 （正しくカウントアップされるはず）