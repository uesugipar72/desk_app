import tkinter as tk
from tkinter import ttk
import sys
import os

# 自作した views パッケージからメイン画面クラスをインポート
from views.main_window import EquipmentManagerMainWindow

def main():
    """アプリケーションのエントリーポイント"""
    # Tkinterのルートウィンドウを生成
    root = tk.Tk()
    
    # 視覚スタイルを「Clam」等に設定して少しモダンな見た目にする（好みに応じて変更可）
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
        
    # メイン画面クラスのインスタンス化（アプリの描画・処理が始まります）
    app = EquipmentManagerMainWindow(root)
    
    # イベントループの開始（画面を閉じられるまで待機）
    root.mainloop()

if __name__ == "__main__":
    # カレントディレクトリをこのファイルの場所に合わせてインポートエラーを防ぐ
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    main()