import sqlite3

class EquipmentManager:
    def get_next_equipment_code(self) -> str:
        """DBのequipment_codeの最大値に1を加えた値を取得"""
        try:
            conn = sqlite3.connect("equipment_management.db")
            cursor = conn.cursor()
            
            # equipment_code の最大値を取得
            cursor.execute("SELECT MAX(equipment_code) FROM equipment")
            max_id = cursor.fetchone()[0]
            
            # 最大値が None（レコードが存在しない）場合は 1 を設定
            next_id = (int(max_id) + 1) if max_id is not None else 1

            return str(next_id).zfill(4)  # 4桁にゼロ埋めして返す

        except sqlite3.Error as e:
            print(f"[ERROR] データベースエラー: {e}")
            return None
        finally:
            conn.close()

# 使用例
manager = EquipmentManager()
next_equipment_code = manager.get_next_equipment_code()
print(f"次の機器ID: {next_equipment_code}")
