import tkinter as tk
from tkcalendar import DateEntry
from datetime import datetime

class NullableDateEntry(DateEntry):
    def __init__(self, master=None, **kwargs):
        kwargs.setdefault("date_pattern", "yyyy-mm-dd")
        super().__init__(master, **kwargs)

        self._default_fg = self.cget("foreground")
        self._var = self["textvariable"] = tk.StringVar()
        self._var.trace_add("write", self._on_write)

    def _on_write(self, *args):
        """ユーザー入力のバリデーション"""
        value = self._var.get().strip()
        if not value:
            self.configure(foreground=self._default_fg)
            return

        try:
            datetime.strptime(value, self.cget("date_pattern").replace("yyyy", "%Y").replace("mm", "%m").replace("dd", "%d"))
            self.configure(foreground=self._default_fg)
        except ValueError:
            self.configure(foreground="red")  # 無効な日付なら赤表示

    def get(self):
        """空白または有効な日付文字列を返す"""
        value = self._var.get().strip()
        if not value:
            return ""
        try:
            datetime.strptime(value, self.cget("date_pattern").replace("yyyy", "%Y").replace("mm", "%m").replace("dd", "%d"))
            return value
        except ValueError:
            return ""  # 無効な日付は空白として扱う

    def set(self, value):
        """値をセット（空白も可）"""
        self._var.set(value or "")
