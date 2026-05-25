def get_connection():
    return sqlite3.connect(DB_PATH)