from tkcalendar import DateEntry
import tkinter as tk
from datetime import datetime


class NullableDateEntry(DateEntry):
    """
    空白を許容し、日付が未設定でも使える DateEntry 拡張クラス。
    - 空欄で初期化・表示が可能
    - 手入力で日付を削除可能
    - 無効な日付は赤文字で警告
    """

    def __init__(self, master=None, **kwargs):
        # フォーマット保存
        self._date_pattern = kwargs.get("date_pattern", "yyyy-mm-dd")
        self._default_fg = kwargs.get("foreground", "black")

        # 初期化
        super().__init__(master, **kwargs)

        # テキスト変数を設定
        self._var = self["textvariable"] or tk.StringVar()
        self.configure(textvariable=self._var)
        self._var.trace_add("write", self._on_write)

    def _on_write(self, *args):
        """
        日付欄の変更監視：無効な日付なら赤表示
        """
        value = self._var.get().strip()
        if not value:
            self.configure(foreground=self._default_fg)
            return
        try:
            datetime.strptime(value, self._date_pattern.replace("yyyy", "%Y").replace("mm", "%m").replace("dd", "%d"))
            self.configure(foreground=self._default_fg)
        except ValueError:
            self.configure(foreground="red")

    def get(self):
        """
        空欄の場合は空文字を返すようにする
        """
        value = super().get().strip()
        return "" if not value else value

    def set_date(self, value):
        """
        valueが空またはNoneなら空欄表示、そうでなければ日付をセット
        """
        if not value:
            self.delete(0, tk.END)
        else:
            super().set_date(value)
