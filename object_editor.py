import os
import pygame
import json
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import colorchooser
from tkinter import simpledialog, messagebox
from objects import RotatingRect, TextLabel
from config import DRAW_W, DRAW_H, SCREEN_W, SCREEN_H

# -----------------------------
# 共通関数
# -----------------------------
import tkinter as tk
from tkinter import messagebox

def confirm_quit():
    """
    True  : はい（保存）
    False : いいえ / キャンセル
    """
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを表示しない

    result = messagebox.askyesnocancel(
        "確認",
        "保存する？"
    )

    root.destroy()
    return result

# -----------------------------
# ファイルダイアログ用関数
# -----------------------------
def tk_file_dialog_open(dialog_func, **options):
    """
    Tk を一時的に作成してファイルダイアログを実行し、
    その後 destroy して結果だけ返す共通関数。

    dialog_func: filedialog.askopenfilename / asksaveasfilename / askdirectory など
    options: ダイアログに渡すキーワード引数
    """
    root = tk.Tk()
    root.withdraw()

    # ダイアログ実行
    result = dialog_func(**options)

    root.destroy()

    return result

# -----------------------------
# mode_select用関数
# -----------------------------
def select_year_version(years, versions):
    """年度とバージョンを選択する小ウィンドウを表示して結果を返す"""
    root = tk.Tk()
    root.withdraw()

    win = tk.Toplevel(root)
    win.title("年度・バージョン選択")
    win.geometry("300x200")
    win.lift()
    win.attributes("-topmost", True)

    result = {"year": None, "version": None}

    # 年度
    tk.Label(win, text="年度").pack(pady=5)
    year_cb = ttk.Combobox(win, values=years, state="readonly")
    year_cb.current(0)
    year_cb.pack()

    # バージョン
    tk.Label(win, text="バージョン").pack(pady=5)
    version_cb = ttk.Combobox(win, values=versions, state="readonly")
    version_cb.current(0)
    version_cb.pack()

    def decide():
        result["year"] = year_cb.get()
        result["version"] = version_cb.get()
        win.destroy()
        root.destroy()

    tk.Button(win, text="決定", command=decide).pack(pady=10)

    win.wait_window()
    return result["year"], result["version"]

# --------------------
# EDIT_OBJECT_WINDOW
# --------------------
def edit_object_window(obj):
    """オブジェクト編集ウィンドウを表示し、編集結果を辞書で返す"""
    root = tk.Tk()
    root.withdraw()

    updated = {}
    win = tk.Toplevel(root)
    win.title("オブジェクト編集")
    win.geometry("400x350")

    win.lift()
    win.attributes("-topmost", True)
    win.after(50, lambda: win.attributes("-topmost", False))
    win.focus_force()

    # No
    tk.Label(win, text='No:').grid(row=0, column=0, sticky="w")
    win.grid_columnconfigure(1, weight=1)
    no_entry = tk.Entry(win)
    no_entry.insert(0, obj.no)
    no_entry.grid(row=0, column=1, sticky="we")

    # Name
    tk.Label(win, text="Name:").grid(row=1, column=0, sticky="w")
    win.grid_columnconfigure(1, weight=1)
    name_entry = tk.Entry(win)

    if isinstance(obj, RotatingRect):
        name_entry.insert(0, obj.name)
    elif isinstance(obj, TextLabel):
        name_entry.insert(0, obj.text)
    name_entry.grid(row=1, column=1, sticky="we")

    # xy
    tk.Label(win, text="x, y:").grid(row=2, column=0, sticky="w")
    win.grid_columnconfigure(1, weight=1)
    xy_entry = tk.Entry(win)

    if isinstance(obj, RotatingRect):
        xy_entry.insert(0, obj.center)
    elif isinstance(obj, TextLabel):
        xy_entry.insert(0, obj.position)
    xy_entry.grid(row=2, column=1, sticky="we")

    # Color
    tk.Label(win, text="Color (R,G,B):").grid(row=3, column=0, sticky="w")
    win.grid_columnconfigure(1, weight=1)
    color_entry = tk.Entry(win)
    color_entry.insert(0, obj.color)
    color_entry.grid(row=3, column=1, sticky="we")

    # Classification
    tk.Label(win, text="Classification:").grid(row=4, column=0, sticky="w")
    win.grid_columnconfigure(1, weight=1)
    class_entry = tk.Entry(win)
    class_entry.insert(0, getattr(obj, "classification", ""))
    class_entry.grid(row=4, column=1, sticky="we")

    # Power
    tk.Label(win, text="Power:").grid(row=5, column=0, sticky="w")
    win.grid_columnconfigure(1, weight=1)
    power_entry = tk.Entry(win)
    power_entry.insert(0, getattr(obj, "power", 0))
    power_entry.grid(row=5, column=1, sticky="we")

    # Tent
    tk.Label(win, text="Tent:").grid(row=6, column=0, sticky="w")
    win.grid_columnconfigure(1, weight=1)
    tent_entry = tk.Entry(win)
    tent_entry.insert(0, getattr(obj, "tent", 0))
    tent_entry.grid(row=6, column=1, sticky="we")

    # Light
    tk.Label(win, text="Light:").grid(row=7, column=0, sticky="w")
    win.grid_columnconfigure(1, weight=1)
    light_entry = tk.Entry(win)
    light_entry.insert(0, getattr(obj, "light", 0))
    light_entry.grid(row=7, column=1, sticky="we")

    def pick_color():
        rgb, hexval = colorchooser.askcolor(color=obj.color, parent=win)
        if rgb:
            color_entry.delete(0, tk.END)
            color_entry.insert(0, f"{int(rgb[0])},{int(rgb[1])},{int(rgb[2])}")

    tk.Button(win, text="色を選ぶ", command=pick_color).grid(row=3, column=2, padx=5)

    def save():
        saved_no = no_entry.get()
        saved_name = name_entry.get()
        
        # 空白やカンマで区切られた文字列をタプルに変換
        entry_xy = xy_entry.get().replace("(", "").replace(")", "")
        # カンマまたはスペースで分割
        parts_xy = [p for p in entry_xy.replace(",", " ").split() if p]

        # 空白やカンマで区切られた文字列をタプルに変換
        entry_color = color_entry.get().replace("(", "").replace(")", "")
        # カンマまたはスペースで分割
        parts_color = [p for p in entry_color.replace(",", " ").split() if p]
        
        # 3要素に満たない場合はエラー
        saved_color = tuple(map(int, parts_color))
        saved_xy = tuple(map(float, parts_xy))
        saved_class = class_entry.get()
        saved_power = power_entry.get()
        saved_tent = tent_entry.get()
        saved_light = light_entry.get()
        # 辞書形式で返す
        updated.clear()
        updated.update({
            "no": saved_no,
            "name": saved_name,
            "text": saved_name,
            "center": saved_xy,
            "position": saved_xy,
            "color": saved_color,
            "classification": saved_class,
            "power": saved_power,
            "tent": saved_tent,
            "light": saved_light
        })

        win.destroy()
        root.destroy()

    def not_save():
        updated.clear()
        updated.update({
            "no": getattr(obj,"no",0),
            "name": getattr(obj,"name",""),
            "text": getattr(obj,"text",""),
            "center": getattr(obj,"center",""),
            "position": getattr(obj,"position",""),
            "color": getattr(obj,"color",(0,0,0)),
            "classification": getattr(obj,"classification",""),
            "power": getattr(obj,"power",0),
            "tent": getattr(obj,"tent",0),
            "light": getattr(obj,"light",0)
        })
        win.destroy()
        root.destroy()

    tk.Button(win, text="保存", command=save).grid(row=8, column=0, columnspan=1, pady=10)
    tk.Label(win, text="Nameは「\\n」で改行して表示").grid(row=8, column=1, padx=10, sticky="w")
    win.bind("<Return>", lambda event: save())
    win.bind("<Escape>", lambda event: not_save())
    win.protocol("WM_DELETE_WINDOW", not_save)
    # win.grab_set()
    win.wait_window()
    return updated


def parse_color(value):
    # タプルならそのまま返す
    if isinstance(value, tuple):
        return value
    #リストならタプルに変換
    if isinstance(value, list):
        try:
            return tuple(int(v) for v in value[:3])
        except:
            return (0,0,0)
    # 文字列の場合
    if isinstance(value, str):
        value = value.strip()
        if value.startswith("(") and value.endswith(")"):
            try:
                return tuple(map(int, value[1:-1].split(",")))
            except:
                return (0,0,0)
        if "," in value:
            try:
                return tuple(map(int, value.split(",")))
            except:
                return (0,0,0)
        if " " in value:
            try:
                return tuple(map(int, value.split()))
            except:
                return (0,0,0)
    return (0,0,0)

# -------------------------
# EDIT_ALL_OBJECTS_WINDOW
# -------------------------
def edit_all_objects_window(objs):
    """全オブジェクト編集ウィンドウを表示し、編集結果を反映する"""
    root = tk.Tk()
    root.withdraw()

    win = tk.Toplevel(root)
    win.title("全オブジェクト編集")
    win.geometry("700x600")

    # --- 最前面化・フォーカス ---
    win.lift()
    win.attributes("-topmost", True)
    win.after(50, lambda: win.attributes("-topmost", False))
    win.focus_force()

    # frame + scroll bar
    frame = tk.Frame(win)
    frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    scrollbar = tk.Scrollbar(frame, orient="vertical")
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Treeviewで一覧表示
    tree = ttk.Treeview(
        frame, columns=("no", "name", "color", "classification", "power", "tent", "light"), show="headings", height=20, yscrollcommand=scrollbar.set
        )
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    # scrollbar と treeview を連携
    scrollbar.config(command=tree.yview)

    tree.heading("no", text="No")
    tree.heading("name", text="Name")
    tree.heading("color", text="Color (R,G,B)")
    tree.heading("classification", text="Classification")
    tree.heading("tent", text="Tent")
    tree.heading("power", text="Power[W]")
    tree.heading("light", text="Light")

    tree.column("no", width=50)
    tree.column("name", width=120)
    tree.column("color", width=120)
    tree.column("classification", width=100)
    tree.column("tent", width=80)
    tree.column("power", width=80)
    tree.column("light", width=80)

    frame.grid(row=0, column=0, columnspan=3, padx=10, pady=10)

    # Treeview に Enter キーをバインド
    tree.bind("<Return>", lambda event: edit_selected())

    # 列ヘッダークリックでソート
    for col in ("no", "name", "color", "classification", "power", "tent", "light"):
        tree.heading(col, text=col.capitalize(), command=lambda c=col: treeview_sort_column(tree, c, False))

    # 初期データを反映
    for i, obj in enumerate(objs):
        color_str = f"{obj.color[0]},{obj.color[1]},{obj.color[2]}"
        tree.insert("", "end", iid=i, values=(obj.no, obj.name, color_str, obj.classification, obj.power, obj.tent, obj.light))

    # --- 1行目を選択 ---
    if objs:
        tree.selection_set("0")  # 選択状態にする
        tree.selection_set("0")  # iid="0" を選択
        tree.focus("0")          # フォーカスも合わせる
        tree.see("0")            # 必要に応じてスクロールして表示
    win.after(100, lambda: tree.focus_set())

    # 編集ボタン
    def edit_selected():
        sel = tree.selection()
        if not sel:
            print("行が選択されていません")
            return

        idx = int(sel[0])
        obj = objs[idx]

        updated = edit_object_window(obj)
        if len(updated) == 0:
            return  # ×閉じる対策

        # updated から各値を取得
        new_no   = updated["no"]
        new_name  = updated["name"]
        new_center = updated["center"]
        new_position = updated["position"]
        new_color = updated["color"]
        new_class = updated["classification"]
        new_power = updated["power"]
        new_tent = updated["tent"]
        new_light = updated["light"]

        # ---- ① TreeView を更新 ----
        color_str = f"{new_color[0]},{new_color[1]},{new_color[2]}"
        tree.item(idx, values=(new_no, new_name, color_str, new_class, new_power, new_tent, new_light))

        # ---- ② objs の中身を更新 ----
        obj.no   = new_no
        obj.name  = new_name
        obj.center  = new_center
        obj.position  = new_position
        obj.color = new_color
        obj.classification = new_class
        obj.power = new_power
        obj.tent = new_tent
        obj.light = new_light

    # 分類ごとに自動色設定
    def auto_assign_colors_window(tree, objs):
        win = tk.Toplevel(root)
        win.title("分類ごとの色設定")
        win.geometry("260x100")
        win.focus_force()


        # --- 分類入力 ---
        tk.Label(win, text="分類名を入力:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_class = tk.Entry(win)
        entry_class.grid(row=0, column=1, padx=0, pady=5)

        selected_color = {"value": None}

        # --- 色選択 ---
        def choose_color():
            classification = entry_class.get().strip()
            if not classification:
                messagebox.showwarning("エラー", "分類名を入力してください。")
                return False

            color = colorchooser.askcolor(title=f"{classification} の色を選択")[0]
            if color is None:
                return False

            selected_color["value"] = tuple(map(int, color))
            return True

        # --- 保存して閉じる ---
        def save_and_close():
            classification = entry_class.get().strip()
            color = selected_color["value"]

            if not classification:
                messagebox.showwarning("エラー", "分類名を入力してください。")
                return

            if color is None:
                messagebox.showwarning("エラー", "色が選択されていません。")
                return

            # objs と Treeview を更新
            for iid in tree.get_children():
                obj = objs[int(iid)]
                if obj.classification == classification:
                    obj.color = color
                    color_str = f"{color[0]},{color[1]},{color[2]}"
                    tree.item(iid, values=(obj.no, obj.name, color_str, obj.classification, obj.power, obj.tent, obj.light))

            win.destroy()

        # --- Enterで決定（色選択→保存→閉じる） ---
        def on_enter(event):
            if choose_color():
                save_and_close()

        # --- Escで閉じる（キャンセル） ---
        def on_escape(event):
            win.destroy()

        # キーバインド
        win.bind("<Return>", on_enter)
        win.bind("<Escape>", on_escape)

        # --- ボタン ---
        tk.Button(win, text="色を選ぶ", width=12,
                command=choose_color).grid(row=1, column=0, padx=15, pady=5)

        tk.Button(win, text="保存して閉じる", width=12,
                command=save_and_close).grid(row=1, column=1, padx=15, pady=5)

        # tk.Button(win, text="キャンセル", width=12,
                # command=win.destroy).grid(row=2, column=0, columnspan=2, pady=5)

        win.wait_window()


    # 自動番号振り分け（beer → 数字、food → 英字）
    def auto_assign_numbers_window(tree, objs):

        win = tk.Toplevel(root)
        win.title("分類ごとの番号振り分け")
        win.geometry("260x140")
        win.focus_force()

        # --- 分類入力 ---
        tk.Label(win, text="分類名を入力:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        entry_class = tk.Entry(win)
        entry_class.grid(row=0, column=1, padx=0, pady=5)

        # 英字番号生成（A → Z → AA → AB ...)
        def alpha_label(index):
            label = ""
            index += 1
            while index > 0:
                index, r = divmod(index - 1, 26)
                label = chr(65 + r) + label
            return label

        # --- 実処理 ---
        def assign_for_class(classification):

            # --- 対象抽出 ---
            items = []
            for iid in tree.get_children():
                obj = objs[int(iid)]
                if obj.classification == classification:
                    cx = obj.center[0] if obj.center else float("inf")
                    cy = obj.center[1] if obj.center else float("inf")
                    items.append((iid, obj, cx, cy))

            if not items:
                messagebox.showinfo("情報", f"分類 '{classification}' の対象がありません。")
                return False

            # --- ソート（x昇順 → y昇順）---
            items.sort(key=lambda t: (t[2], t[3]))

            # --- 番号振り分け ---
            for idx, (iid, obj, _, _) in enumerate(items):

                if classification == "beer":
                    new_no = str(idx + 1)

                elif classification == "food":
                    new_no = alpha_label(idx)

                else:
                    messagebox.showinfo("対応外", "対応している分類は 'beer' と 'food' だけです。")
                    return False

                obj.no = new_no

                # Treeview更新
                color_str = f"{obj.color[0]},{obj.color[1]},{obj.color[2]}"
                tree.item(iid, values=(obj.no, obj.name, color_str, obj.classification, obj.power, obj.tent, obj.light))

            return True

        # --- 保存して閉じる ---
        def save_and_close():
            classification = entry_class.get().strip()

            if not classification:
                messagebox.showwarning("エラー", "分類名を入力してください。")
                return

            if assign_for_class(classification):
                win.destroy()

        # --- Enterで決定 → 保存して閉じる ---
        def on_enter(event):
            save_and_close()

        # --- ESCでキャンセル ---
        def on_escape(event):
            win.destroy()

        win.bind("<Return>", on_enter)
        win.bind("<Escape>", on_escape)

        # --- ボタン ---
        tk.Button(win, text="番号振り分け", width=12,
                command=save_and_close).grid(row=1, column=0, padx=10, pady=10)

        tk.Button(win, text="閉じる", width=12,
                command=win.destroy).grid(row=1, column=1, padx=10, pady=10)

        win.wait_window()


    def treeview_sort_column(tv, col, reverse):
        def sort_key(v):
            try:
                return (0, int(v))
            except ValueError:
                return (1, v)

        items = [(sort_key(tv.set(k, col)), k) for k in tv.get_children('')]
        items.sort(key=lambda t: t[0], reverse=reverse)

        for index, (_, k) in enumerate(items):
            tv.move(k, '', index)

        tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))


    # 保存ボタン（全体確定）
    def save_all(*args):
        # Treeview の全行を objs に書き戻す
        for iid in tree.get_children():
            no, name, color_text, classification, power, tent, light = tree.item(iid, "values")
            obj = objs[int(iid)]
            obj.no = no
            obj.name = name
            obj.color = parse_color(color_text)
            obj.classification = classification
            obj.power = power
            obj.tent = tent
            obj.light = light
        win.destroy()
        root.destroy()


    # edit_all_objects_window 内でのボタン
    btn_frame = tk.Frame(win)
    btn_frame.grid(row=1, column=0, padx=1, pady=5, sticky="ew")

    tk.Button(btn_frame, text="選択行を編集", width=25, command=edit_selected).pack(pady=5)
    tk.Button(btn_frame, text="分類ごとに自動色振り分け", width=25,
            command=lambda: auto_assign_colors_window(tree, objs)).pack(pady=5)
    tk.Button(btn_frame, text="分類ごとに自動番号振り分け", width=25,
            command=lambda: auto_assign_numbers_window(tree, objs)).pack(pady=5)
    tk.Button(btn_frame, text="閉じて保存", width=25, command=save_all).pack(pady=5)

    win.bind("<Escape>", save_all)
    win.protocol("WM_DELETE_WINDOW", save_all)

    # win.grab_set() #ほかの操作をブロック
    win.wait_window() #モーダル操作
    return objs

# -----------------------------
# POWER計算/表示（全体形式）
# -----------------------------
def show_power_table_with_category(rects, categories, point_in_category):
    """
    RotatingRect の power を表形式で表示し、カテゴリごとの power 総計も表示
    rects: RotatingRect のリスト
    categories: カテゴリオブジェクトのリスト
    point_in_category: 矩形がカテゴリ内にあるか判定する関数
    """
    def categories_name_containing_rect(center, categories):
        """矩形(center)がカテゴリ(cat)内にあるか判定"""
        return [cat.name for cat in categories if point_in_category(center, cat)]

    root = tk.Tk()
    root.withdraw()

    win = tk.Toplevel(root)
    win.title("Power Table with Category")
    win.geometry("800x500")

    # --- 最前面化・フォーカス ---
    win.lift()
    win.attributes("-topmost", True)
    win.after(50, lambda: win.attributes("-topmost", False))
    win.focus_force()

    # frame + scrollbar
    frame = tk.Frame(win)
    frame.pack(fill="both", expand=True, padx=10, pady=10)
    scrollbar = tk.Scrollbar(frame, orient="vertical")
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Treeview作成
    tree = ttk.Treeview(
        frame,
        columns=("No", "Name", "Power", "Tent", "Light", "Categories"),
        show="headings",
        yscrollcommand=scrollbar.set,
        height=20
    )
    tree.pack(side=tk.LEFT, fill="both", expand=True)
    scrollbar.config(command=tree.yview)

    # 列ヘッダ
    tree.heading("No", text="No", command=lambda: treeview_sort_column(tree, "No", False))
    tree.heading("Name", text="Name", command=lambda: treeview_sort_column(tree, "Name", False))
    tree.heading("Power", text="Power[W]", command=lambda: treeview_sort_column(tree, "Power", False))
    tree.heading("Tent", text="Tent", command=lambda: treeview_sort_column(tree, "Tent", False))
    tree.heading("Light", text="Light", command=lambda: treeview_sort_column(tree, "Light", False))
    tree.heading("Categories", text="Categories", command=lambda: treeview_sort_column(tree, "Categories", False))

    tree.column("No", width=50, anchor="center")
    tree.column("Name", width=200, anchor="w")
    tree.column("Power", width=80, anchor="center")
    tree.column("Tent", width=80, anchor="center")
    tree.column("Light", width=80, anchor="center")
    tree.column("Categories", width=80, anchor="w")

    # Treeviewにデータ挿入
    rect_iid_map = {}
    for idx, r in enumerate(rects):
        cats = categories_name_containing_rect(r.center, categories)
        iid = f"rect_{r.no}_{idx}"
        tree.insert("", "end", iid=iid, values=(r.no, r.name, r.power, r.tent, r.light, ", ".join(cats)))
        rect_iid_map[iid] = r

    # --- 初期行をアクティブにする ---
    if rect_iid_map:
        first_iid = list(rect_iid_map.keys())[0]
        tree.selection_set(first_iid)  # 選択状態にする
        tree.focus(first_iid)          # フォーカスを合わせる
        tree.see(first_iid)            # 必要に応じてスクロール
        win.after(100, lambda: tree.focus_set())  # Enterキーが有効になるようにフォーカス

    # カテゴリごとの power 総計ラベル
    totals_label = tk.Label(frame, text="", justify="left", anchor="nw")
    totals_label.pack(side="left", fill="y", padx=25, pady=5)


    def update_category_totals():
        totals = {}
        no_cat_total = 0
        total_power = 0

        # --- カテゴリ一覧を一度だけ作る ---
        unique = {}
        for cc in categories:
            if getattr(cc, "alert", False):
                continue
            key = (cc.name, cc.power_limit)
            if key not in unique:
                unique[key] = cc

        sorted_categories = sorted(unique.values(), key=lambda cc: cc.name)

        # --- rect 処理 ---
        for r in rects:
            try:
                r_power = int(r.power)
            except (ValueError, TypeError):
                r_power = 0

            total_power += r_power

            cats = categories_name_containing_rect(r.center, sorted_categories)

            if not cats:
                no_cat_total += r_power
            else:
                for cat_name in cats:
                    totals[cat_name] = totals.get(cat_name, 0) + r_power

        # --- 表示 ---
        text_lines = [f"各パネル総電力\n電力合計: {total_power} [W]"]

        for k, v in totals.items():
            text_lines.append(f"{k}: {v} [W]")

        if no_cat_total > 0:
            text_lines.append(f"注意!_カテゴリなし: {no_cat_total} [W]")

        totals_label.config(
            text="\n".join(text_lines) if totals or no_cat_total else "データなし"
        )
    update_category_totals()

    # 編集用：ダブルクリックで power 編集
    def edit_power(event):
        selected = tree.selection()
        if not selected:
            return
        item_id = selected[0]
        r = rect_iid_map[item_id]
        try:
            current_power = int(r.power)
        except ValueError:
            current_power = 0
        new_power = simpledialog.askinteger(
            "Edit Power",
            f"Edit Power / {r.no}: {r.name}\n", initialvalue=current_power
        )
        if new_power is not None:
            r.power = int(new_power)
            cats = categories_name_containing_rect(r.center, categories)
            tree.item(item_id, values=(r.no, r.name, r.power, r.tent, r.light, ", ".join(cats)))
            update_category_totals()

    def treeview_sort_column(tv, col, reverse=False):
        """任意列（No / Name / Color / Categories）でソート"""
        data = []
        for iid in tv.get_children():
            val = tv.set(iid, col)
            # --- 列別ソートキー生成 ---
            if col == "No":
                # 数値として扱えるなら数値 → ダメなら文字列
                try:
                    sort_key = int(val)
                except ValueError:
                    sort_key = float('inf')  # 数値でなければ後ろへ
            elif col == "Color":
                # "255,100,50" → (255,100,50) に変換してソート
                try:
                    rgb = tuple(int(x) for x in val.split(","))
                    sort_key = rgb
                except Exception:
                    sort_key = (999, 999, 999)
            else:
                # Name / Categories は文字列ソート
                sort_key = val.lower() if val else "zzz"  # 空文字は後ろ
            data.append((sort_key, iid))

        # --- 実際のソート ---
        data.sort(key=lambda x: x[0], reverse=reverse)
        # --- 並び替え ---
        for index, (_, iid) in enumerate(data):
            tv.move(iid, '', index)
        # 次のクリックで昇順⇔降順を切り替え
        tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))
    

    tree.bind("<Double-1>", edit_power)
    tree.bind("<Return>", edit_power)

    # 閉じて保存ボタン
    def close_window():
        win.destroy()
        root.destroy()

    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=5)
    tk.Button(btn_frame, text="閉じて保存", width=25, height=3, command=close_window).pack()

    win.bind("<Escape>", lambda e: close_window())
    win.protocol("WM_DELETE_WINDOW", close_window)

    # モーダル表示
    win.wait_window()


# -----------------
# ポリゴン編集ウィンドウ
# -----------------
def edit_polygon_window(poly):
    root = tk.Tk()
    root.withdraw()

    win = tk.Toplevel(root)
    win.title("ポリゴン編集")
    win.geometry("360x180")

    win.lift()
    win.attributes("-topmost", True)
    win.after(50, lambda: win.attributes("-topmost", False))
    win.focus_force()

    # -------------------------
    # Color
    # -------------------------
    tk.Label(win, text="Color (r,g,b):").grid(row=0, column=0, sticky="w", padx=5, pady=5)

    color_entry = tk.Entry(win)
    color_entry.insert(0, str(poly.color))
    color_entry.grid(row=0, column=1, sticky="we", padx=5)

    def pick_color():
        c = colorchooser.askcolor(color=poly.color)
        if c[0]:
            rgb = tuple(int(v) for v in c[0])
            color_entry.delete(0, tk.END)
            color_entry.insert(0, str(rgb))

    tk.Button(win, text="色変更", command=pick_color).grid(row=0, column=2, padx=5)

    # -------------------------
    # Width
    # -------------------------
    tk.Label(win, text="Line Width:").grid(row=1, column=0, sticky="w", padx=5, pady=5)

    width_entry = tk.Entry(win, width=5)
    width_entry.insert(0, str(getattr(poly, "width", 1)))
    width_entry.grid(row=1, column=1, sticky="w", padx=5)

    # -------------------------
    # Save / Cancel
    # -------------------------
    def save():
        # color
        entry_color = color_entry.get().replace("(", "").replace(")", "")
        parts = [p for p in entry_color.replace(",", " ").split() if p]
        try:
            color = tuple(map(int, parts))
            if len(color) == 3:
                poly.color = color
        except Exception:
            pass

        # width
        try:
            poly.width = int(width_entry.get())
        except Exception:
            pass

        win.destroy()

    def not_save():
        win.destroy()

    tk.Button(win, text="保存", command=save).grid(row=2, column=0, pady=10)
    tk.Button(win, text="キャンセル", command=not_save).grid(row=2, column=1, pady=10)    

    # -------------------------
    # Key bindings
    # -------------------------
    win.bind("<Return>", lambda event: save())
    win.bind("<Escape>", lambda event: not_save())
    win.protocol("WM_DELETE_WINDOW", not_save)

    win.grid_columnconfigure(1, weight=1)

    # ★ pygame 併用時に必須
    root.wait_window(win)
    root.destroy()


# ---------------
# カテゴリモード用
# ---------------
def edit_category_dialog(cat):
    """カテゴリ編集ウィンドウ（名前 + アラート + カラー）"""
    root = tk.Tk()
    root.withdraw()

    updated = {}
    win = tk.Toplevel(root)
    win.title("カテゴリ編集")

    win.lift()
    win.attributes("-topmost", True)
    win.after(50, lambda: win.attributes("-topmost", False))
    win.focus_force()

    # --- 初期値 ---
    alert_state = tk.BooleanVar(value=cat.alert)

    # --- Name ---
    tk.Label(win, text="カテゴリ名:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
    name_entry = tk.Entry(win)
    name_entry.insert(0, cat.name)
    name_entry.grid(row=0, column=1, sticky="w", padx=10, pady=5)

    # --- Power Limit ---
    tk.Label(win, text="電力上限:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
    power_limit_entry = tk.Entry(win)
    power_limit_entry.insert(0, cat.power_limit)
    power_limit_entry.grid(row=1, column=1, sticky="w", padx=10, pady=5)

    # --- Alert ---
    tk.Label(win, text="アラート:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
    alert_label = tk.Label(win, text=f"現在: {'ON' if alert_state.get() else 'OFF'}")
    alert_label.grid(row=2, column=1, sticky="w", padx=10, pady=5)

    def toggle_alert():
        alert_state.set(not alert_state.get())
        toggle_btn.config(text="アラート ON" if alert_state.get() else "アラート OFF")
        alert_label.config(text=f"現在: {'ON' if alert_state.get() else 'OFF'}")

    toggle_btn = tk.Button(
        win,
        text="アラート ON" if alert_state.get() else "アラート OFF",
        width=14,
        command=toggle_alert
    )
    toggle_btn.grid(row=2, column=2, columnspan=2, sticky="w", padx=10, pady=5)

    # --- Color ---
    tk.Label(win, text="カラー (R,G,B):").grid(
        row=3, column=0, sticky="w", padx=10, pady=5
    )

    color_entry = tk.Entry(win)
    color_entry.insert(0, f"{cat.color[0]},{cat.color[1]},{cat.color[2]}")
    color_entry.grid(
        row=3, column=1, sticky="w", padx=10, pady=5
    )

    def pick_color():
        rgb, hexval = colorchooser.askcolor(color=tuple(cat.color), parent=win)
        if rgb:
            color_entry.delete(0, tk.END)
            color_entry.insert(0, f"{int(rgb[0])},{int(rgb[1])},{int(rgb[2])}")

    tk.Button(win, text="色を選ぶ", command=pick_color).grid(
        row=3, column=2, sticky="w", padx=10, pady=5
    )


    # --- 保存 ---
    def save():
        updated.clear()

        # color_entry の文字列 "R,G,B" をパース
        try:
            rgb_text = color_entry.get().split(",")
            r = max(0, min(255, int(rgb_text[0].strip())))
            g = max(0, min(255, int(rgb_text[1].strip())))
            b = max(0, min(255, int(rgb_text[2].strip())))
        except:
            # 読み取りに失敗したら元の色を使う
            r, g, b = cat.color
            print("error")

        updated.update({
            "name": name_entry.get(),
            "alert": alert_state.get(),
            "color": [r, g, b],   # JSONの color に対応
            "power_limit": power_limit_entry.get(),
        })

        print("saved")
        win.destroy()
        root.destroy()

    # --- キャンセル ---
    def not_save():
        updated.clear()
        updated.update({
            "name": cat.name,
            "alert": cat.alert,
            "color": cat.color,
            "power_limit": cat.power_limit,
        })
        print("not saved")
        win.destroy()
        root.destroy()

    # --- Save/Cancel Buttons ---
    frame_save = tk.Frame(win)
    frame_save.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=10)
    tk.Button(frame_save, text="保存", width=10, command=save).pack(side="left", padx=5)
    tk.Button(frame_save, text="キャンセル", width=10, command=not_save).pack(side="left", padx=5)

    # --- Keybinds ---
    win.bind("<Return>", lambda e: save())
    win.bind("<Escape>", lambda e: not_save())

    win.protocol("WM_DELETE_WINDOW", not_save)

    win.wait_window()
    return updated

