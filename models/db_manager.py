import sqlite3
import os
import json
from contextlib import contextmanager
from typing import Iterator

class DBManager:
    """データベース接続を管理するベースクラス"""
    
    # 共通のconfig読み込み
    _config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    try:
        with open(_config_path, "r", encoding="utf-8") as f:
            _config = json.load(f)
        DB_NAME = _config.get("db_name", "default.db")
    except FileNotFoundError:
        DB_NAME = "default.db"

    @classmethod
    @contextmanager
    def get_cursor(cls) -> Iterator[sqlite3.Cursor]:
        """SQLを実行するためのカーソルを提供するコンテキストマネージャ"""
        conn = sqlite3.connect(cls.DB_NAME)
        try:
            yield conn.cursor()
            conn.commit()  # 更新系処理のために一応commitを入れる
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()