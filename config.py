import tkinter as tk

# --- 設定 ---
font_path = "C:/Windows/Fonts/meiryo.ttc"

# 内部描画解像度（固定）
DRAW_W, DRAW_H = 1920, 1080

# 初期ウィンドウサイズ（ユーザーが見るサイズ）
SCREEN_W, SCREEN_H = 1920, 1080

# スケール係数
SCALE_X = SCREEN_W / DRAW_W
SCALE_Y = SCREEN_H / DRAW_H

# JSON保存先
CATEGORIES_FILE = "categories.json"
RECTS_FILE = "rects.json"

# 過去開催JSON保存ディレクトリ
PAST_EVENT_DIR = "past_event_data"

# 過去開催JSONリスト
PAST_EVENT_DATA_LIST = "past_event_data_list.json"

root = tk.Tk() #tk.Tk() はアプリ全体で1回だけ作る
root.withdraw()  # 常に隠しておく

# DELETE/UNDO用
last_deleted_obj = None

# 右クリックメニュー項目（形状追加）
MENU_ITEMS_ADD_SHAPE = [
    ("Rectangle", "add_rect"),
    ("Circle",    "add_circle"),
    ("Polygon",   "add_polygon"),
]

