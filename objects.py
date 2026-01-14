import pygame
import json
import os
import math
import csv
import tkinter as tk
from abc import ABC, abstractmethod
from os.path import basename
from tkinter import filedialog
from tkinter import colorchooser
from utils import (get_rotated_rect_points, count_total_by_classification, categories_power_list, point_in_category, convert_mouse_to_draw_coords,
                   point_to_segment_distance, hit_test_polyline)
from config import CATEGORIES_FILE, RECTS_FILE, font_path, SCREEN_W, SCREEN_H

# -----------------------------
# データ管理
# -----------------------------
class DataManager:
    @classmethod
    def save_all(cls, rects, texts, categories, polygons, filename=None):
        """rect, text, category をまとめて保存"""
        from object_editor import tk_file_dialog_open

        if filename is not None:
            filename = tk_file_dialog_open(
                filedialog.asksaveasfilename,
                title="保存先を選択",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=filename
            )

        if filename is None:
            filename = tk_file_dialog_open(
                filedialog.asksaveasfilename,
                title="保存先を選択",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=""
            )

        if not filename:
            print("保存キャンセル")
            return

        data = {
            "rects":      [r.to_dict() for r in rects],
            "texts":      [t.to_dict() for t in texts],
            "categories": [c.to_dict() for c in categories],
            "polygons":     [s.to_dict() for s in polygons],
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print("Saved all ->", filename)

    @classmethod
    def load_all(cls, filename=None):
        """rect, text, category をまとめて読み込み"""
        from object_editor import tk_file_dialog_open

        if filename is None:
            filename = tk_file_dialog_open(
                filedialog.askopenfilename,
                title="読み込むファイルを選択",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )


        if not filename:
            print("読み込みキャンセル")
            return [], [], [], [], "", ""

        if not os.path.exists(filename):
            print("ファイルなし:", filename)
            return [], [], [], [], "", ""

        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        print("Loaded all ->", filename)

        rects      = [RotatingRect.from_dict(d)  for d in data.get("rects", [])]
        texts      = [TextLabel.from_dict(d)     for d in data.get("texts", [])]
        categories = [CategoryShape.from_dict(d) for d in data.get("categories", [])]
        polygons   = [PolygonShape.from_dict(d)         for d in data.get("polygons", [])]

        full_path = filename
        filename = basename(filename)

        return rects, texts, categories, polygons, filename, full_path


# -----------------------------
# オブジェクト新規追加メニュー（右クリック）
# -----------------------------
class ContextMenu:
    def __init__(self, items, pos):
        """
        items : [(label, action), ...]
        pos   : (x, y)
        """
        self.items = items
        self.pos = pos
        self.width = 160
        self.item_h = 24
        self.visible = True
        self.hover = -1

    def _update_hover(self, mouse_pos):
        """マウス位置から hover index を計算"""
        mx, my = mouse_pos
        x, y = self.pos

        if x <= mx <= x + self.width:
            idx = (my - y) // self.item_h
            if 0 <= idx < len(self.items):
                self.hover = idx
                return

        self.hover = -1

    def draw(self, screen, font):
        if not self.visible:
            return

        x, y = self.pos
        h = len(self.items) * self.item_h

        # 背景
        pygame.draw.rect(screen, (230, 230, 230), (x, y, self.width, h))
        pygame.draw.rect(screen, (0, 0, 0), (x, y, self.width, h), 1)

        # 各項目
        for i, (label, _) in enumerate(self.items):
            r_y = y + i * self.item_h

            if i == self.hover:
                pygame.draw.rect(
                    screen,
                    (200, 200, 200),
                    (x, r_y, self.width, self.item_h)
                )

            txt = font.render(label, True, (0, 0, 0))
            screen.blit(txt, (x + 6, r_y + 4))

    def handle_event(self, event):
        if not self.visible:
            return None

        # hover 更新（移動時）
        if event.type == pygame.MOUSEMOTION:
            self._update_hover(event.pos)

        # クリック判定
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # 念のためクリック時にも hover 再計算
                self._update_hover(event.pos)

                if self.hover != -1:
                    label, action = self.items[self.hover]
                    print("コンテキストメニュー選択:", label)
                    self.visible = False
                    return action
                else:
                    # メニュー外クリック
                    self.visible = False

            else:
                # 左クリック以外（右クリックなど）でも閉じる
                self.visible = False

        # ESC で閉じる
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.visible = False

        return None


# -----------------------------
# アクティブインフォメーションテキスト
# -----------------------------
class InfoPanel:
    def __init__(self, font, width, height):
        self.font = font
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)

        self._cache_key = None
        self._dirty = True

    def mark_dirty(self):
        self._dirty = True

    def update(
        self,
        active,
        active_rects,
        rects,
        categories,
        categories_name_containing_rect,
        count_total_by_classification,
        categories_power_list,
        point_in_category,
    ):
        """
        内容が変わったときだけ Surface を作り直す
        """

        # --- キャッシュキー（最低限でOK） ---
        key = (
            id(active),
            tuple(r.no for r in active_rects) if active_rects else None,
            tuple((r.no, r.power, r.classification) for r in rects),
        )

        if key == self._cache_key and not self._dirty:
            return

        self._cache_key = key
        self._dirty = False

        surf = self.surface
        surf.fill((0, 0, 0, 0))  # 透明クリア

        line_h = 20

        # =========================================================
        # アクティブ情報
        # =========================================================
        y = 50

        def line(text, x=10, color=(0, 0, 0)):
            nonlocal y
            surf.blit(self.font.render(text, True, color), (x, y))
            y += line_h

        if isinstance(active, RotatingRect):
            info_name = active.name.replace("\\n", "").replace("\n", "")

            line(f"no: {active.no}")
            line(f"name: {info_name}")
            line("area:")

            categories_name_list = categories_name_containing_rect(
                active.center, categories
            ) or []
            category_names = ", ".join(sorted(set(categories_name_list))) or "None"
            surf.blit(self.font.render(category_names, True, (0, 0, 0)), (55, 90))

            line(f"classification: {active.classification}")
            line(f"power [W]: {active.power}")
            line(f"rect_size: {active.size}")
            line(f"angle: {active.angle}")
            line(f"font_size: {active.font_size}")
            line(f"name_angle: {active.name_angle}")
            line(f"rect_position: {active.center}")

            name_pos = (
                active.name_pos[0] + active.center[0],
                active.name_pos[1] + active.center[1],
            )
            line(f"name_position: {name_pos}")

        elif active_rects:
            active_rects = sorted(active_rects, key=lambda r: r.no)

            ids = ", ".join(str(r.no) for r in active_rects)
            names = ", ".join(
                r.name.replace("\\n", "").replace("\n", "") for r in active_rects
            )
            classes = ", ".join(sorted({r.classification for r in active_rects}))
            powers = ", ".join(sorted(str(r.power) for r in active_rects))
            rect_sizes = ", ".join(sorted({str(r.size) for r in active_rects}))
            font_sizes = ", ".join(sorted({str(r.font_size) for r in active_rects}))

            line(f"no: {ids}")
            line(f"name: {names}")
            line("area:")

            all_category_names = [
                name
                for r in active_rects
                for name in (categories_name_containing_rect(r.center, categories) or [])
            ]
            category_names = ", ".join(sorted(set(all_category_names))) or "None"
            surf.blit(self.font.render(category_names, True, (0, 0, 0)), (55, 90))

            line(f"classification: {classes}")
            line(f"power [W]: {powers}")
            line(f"rect_size: {rect_sizes}")
            line("angle:")
            line(f"font_size: {font_sizes}")
            line("name_angle:")
            line("center:")

        # =========================================================
        # 各クラス毎の総数（右上）
        # =========================================================
        total_counts = count_total_by_classification(rects)

        base_x = surf.get_width() - 10
        y = 50

        for key in sorted(total_counts.keys()):
            text = f"{key}: {total_counts[key]}"
            ts = self.font.render(text, True, (0, 0, 0))
            surf.blit(ts, (base_x - ts.get_width(), y))
            y += line_h

        # =========================================================
        # 電力合計
        # =========================================================
        power_totals, sorted_categories = categories_power_list(
            rects, categories, point_in_category
        )

        power_limit_map = {c.name: c.power_limit for c in sorted_categories}

        base_y = 290

        for i, (name, power) in enumerate(sorted(power_totals.items())):
            limit = int(power_limit_map.get(name, 0))
            color = (255, 0, 0) if limit > 0 and power > limit else (0, 0, 0)
            text = f"{name}: {power}[W]/{limit}[W]"
            surf.blit(
                self.font.render(text, True, color),
                (10, base_y + i * line_h),
            )

    def draw(self, screen, pos=(0, 0)):
        screen.blit(self.surface, pos)

# -----------------------------
# カテゴリ多角形クラス
# -----------------------------
class CategoryShape:
    def __init__(self, name, color=(150,200,250), points=None, alert=False, power_limit=0):
        self.name = name
        self.color = tuple(color)
        self.points = list(points) if points else []
        self.alert = alert
        self.power_limit = power_limit

    def to_dict(self):
        """JSON保存用辞書"""
        return {"name": self.name, "color": list(self.color), "points": [list(p) for p in self.points], "alert": self.alert, "power_limit": self.power_limit}

    @classmethod
    def from_dict(cls, d):
        """JSON読み込み用"""
        return cls(
            name=d.get("name","category"),
            color=tuple(d.get("color",(150,200,250))), 
            points=[tuple(p) for p in d.get("points",[])],
            alert=d.get("alert", False),
            power_limit=d.get("power_limit", 0),
        )

    def draw_category(self, screen, font, active=False, active_vertex=None, show_names=True, show_vertices=True):
        """画面に多角形描画"""
        if not self.points:
            return
        col = (255,100,100) if active else self.color
        pygame.draw.polygon(screen, col, self.points, 3)
        
        # 頂点表示
        if show_vertices:
            for i,(x,y) in enumerate(self.points):
                if active and active_vertex == i:
                    pygame.draw.circle(screen, (255,0,0), (int(x),int(y)), 6)  # 選択頂点赤
                else:
                    pygame.draw.circle(screen, (0,0,255), (int(x),int(y)), 6)  # 他の頂点青
        
        # 多角形名を重心付近に表示
        if show_names:
            cx = sum(p[0] for p in self.points)/len(self.points)
            cy = sum(p[1] for p in self.points)/len(self.points)
            name_surf = font.render(self.name, True, (0,0,0))
            rect = name_surf.get_rect(center=(cx, cy))
            screen.blit(name_surf, rect)

        if active:
            # 頂点番号表示
            for i,(x,y) in enumerate(self.points):
                no_surf = font.render(str(i), True, (0,0,0))
                rect = no_surf.get_rect(center=(x, y - 12))
                screen.blit(no_surf, rect)

    # @classmethod
    # def save_categories(cls, categories, filename=CATEGORIES_FILE):
    #     with open(filename, "w", encoding="utf-8") as f:
    #         json.dump([c.to_dict() for c in categories], f, ensure_ascii=False, indent=2)
    #     print("Saved categories ->", filename)

    # @classmethod
    # def load_categories(cls, filename=CATEGORIES_FILE):
    #     if not os.path.exists(filename):
    #         return []
    #     with open(filename, "r", encoding="utf-8") as f:
    #         data = json.load(f)
    #     return [CategoryShape.from_dict(d) for d in data]

# -----------------------------
# テキストクラス
# -----------------------------
class TextLabel:
    def __init__(self, no="0", text="Text", position=(100,100), font_size=20, color=(0,0,0), angle=0, classification="Text", power="0", locked=False):
        self.no = no
        self.text = text
        self.position = tuple(position)
        self.font_size = font_size
        self.color = tuple(color)
        self.angle = angle
        self.drag_offset = (0,0)
        self.classification = classification
        self.power = power
        self.locked = locked


    def to_dict(self):
        """JSON保存用"""
        return {
            "no": self.no,
            "text": self.text,
            "position": list(self.position),
            "font_size": self.font_size,
            "color": list(self.color),
            "angle": self.angle,
            "locked": self.locked,
        }
    
    @classmethod
    def from_dict(cls, d):
        """JSON読み込み用"""
        return cls(
            no=d.get("no","No"),
            text=d.get("text","Label"),
            position=tuple(d.get("position",(100,100))),
            font_size=d.get("font_size",20),
            color=tuple(d.get("color",(0,0,0))),
            angle=d.get("angle",0),
            locked=d.get("locked", False),
        )
    
    def draw_texts(self, screen, font_path, active=False):
        """文字描画"""
        if active:
            text_color = (0,0,255) # 青
        else:
            text_color = self.color

        font = pygame.font.Font(font_path, self.font_size)
        text_surf = font.render(self.text, True, text_color)
        rotated_surf = pygame.transform.rotate(text_surf, -self.angle)
        rect = rotated_surf.get_rect(midleft=self.position)
        screen.blit(rotated_surf, rect)

    def edit_properties(self):
        """プロパティ編集ダイアログ表示"""
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        win = tk.Toplevel(root)
        win.title("テキストプロパティ編集")

        # --- テキスト編集 ---
        tk.Label(win, text="Text:").grid(row=0, column=0, sticky="w")
        text_entry = tk.Entry(win)
        text_entry.insert(0, self.text)
        text_entry.grid(row=0, column=1)

        # # --- 最前面化・フォーカス ---
        # win.lift()
        # win.attributes("-topmost", True)
        # win.after(50, lambda: win.attributes("-topmost", False))
        # win.focus_force()

        # --- フォントサイズ ---
        tk.Label(win, text="Font Size:").grid(row=0, column=0, sticky="w")
        size_entry = tk.Entry(win)
        size_entry.insert(0, str(self.font_size))
        size_entry.grid(row=0, column=1)

        # --- 色 ---
        tk.Label(win, text="Color (R,G,B):").grid(row=1, column=0, sticky="w")
        color_entry = tk.Entry(win)
        color_entry.insert(0, f"{self.color[0]},{self.color[1]},{self.color[2]}")
        color_entry.grid(row=1, column=1)

        # 色選択ボタン
        def pick_color():
            rgb, hexval = colorchooser.askcolor(color=self.color, parent=win)
            if rgb:
                color_entry.delete(0, tk.END)
                color_entry.insert(0, f"{int(rgb[0])},{int(rgb[1])},{int(rgb[2])}")

        tk.Button(win, text="色を選ぶ", command=pick_color).grid(row=1, column=2, padx=5)

        # --- 保存ボタン ---
        def save():
            self.text = text_entry.get()
            self.font_size = int(size_entry.get())
            entry_color = color_entry.get().replace("(", "").replace(")", "")
            parts = [p for p in entry_color.replace(",", " ").split() if p]
            self.color = tuple(map(int, parts))
            win.destroy()
            root.destroy()

        tk.Button(win, text="保存", command=save).grid(row=2, column=0, columnspan=2, pady=10)

        win.grab_set()
        win.wait_window()

    def contains_point(self, p, font_path):
        """点 p がテキスト内にあるか判定"""
        # フォント生成
        font = pygame.font.Font(font_path, self.font_size)
        # テキストサーフェス作成
        text_surf = font.render(self.text, True, self.color)
        # 回転
        rotated_surf = pygame.transform.rotate(text_surf, -self.angle)
        # 回転後の矩形取得（中心は self.position）
        rect = rotated_surf.get_rect(midleft=self.position)
        # 点が矩形内にあるか判定
        return rect.collidepoint(p)


# -----------------------------
# 回転四角形クラス（マップ上オブジェクト）
# -----------------------------
class RotatingRect:
    def __init__(
            self, 
            no=0, 
            name="rect", 
            name_pos=(20,-10), 
            name_color=(0,0,0), 
            name_angle=0, 
            font_size=15, 
            power=0, 
            center=(100,100), 
            size=(25,25), 
            color=(100,200,100), 
            angle=0, 
            classification="beer", 
            name_pos_active=False,
            tent=0,
            light=0,
            ):
        self.no = no
        self.name = name
        self.name_pos = tuple(name_pos)
        self.name_color = tuple(name_color)
        self.name_angle = name_angle
        self.font_size = font_size
        self.power = power
        self.center = tuple(center)
        self.size = tuple(size)
        self.color = tuple(color)
        self.angle = angle
        self.dragging = False
        self.drag_offset = (0,0)
        self.classification = classification
        self.name_pos_active = name_pos_active
        self.tent = tent
        self.light = light

        self._cache_rect_img = None
        self._cache_rect_angle = None
        self._cache_rect_color = None
        self._cache_name_img = None
        self._cache_name_angle = None
        self._cache_name_color = None
        self._cache_name_pos_active = None
        self._cache_no_font = None
        self._cache_no_font_size = None
        self._cache_name_font = None
        self._cache_name_font_size = None
        self._cache_categories = None
        self._cache_center = None
        self._cache_categories = None
        self._cache_center = None
        self._cache_categories = None
        self.prev_dirty = []

    def to_dict(self):
        """JSON保存用"""
        return {
            "no": self.no,
            "name": self.name,
            "name_pos": list(self.name_pos),
            "name_color": list(self.name_color),
            "name_angle": self.name_angle,
            "font_size": self.font_size,
            "power": self.power,
            "center": list(self.center),
            "size": list(self.size),
            "color": list(self.color),
            "angle": self.angle,
            "classification": self.classification,
            "tent": self.tent,
            "light": self.light,
        }

    @classmethod
    def from_dict(cls, d):
        """JSON読み込み用"""
        return cls(
            no=d.get("no",0),  # 番号
            name=d.get("name","rect"),  # 名前
            name_pos=tuple(d.get("name_pos",(0,0))), # 名前位置
            name_angle=d.get("name_angle",0), # 名前角度
            font_size=d.get("font_size",0), #フォントサイズ
            power=d.get("power",0),  # パワー
            center=tuple(d.get("center",(100,100))), # 中心座標
            size=tuple(d.get("size",(50,50))),  # サイズ
            color=tuple(d.get("color",(100,200,100))),  # 色
            angle=d.get("angle",0), # 回転角度
            classification=d.get("classification","beer"), # 分類    
            tent=d.get("tent",0), # テント
            light=d.get("light",0) # 投光器                    
        )

    @classmethod
    def save_rects_as_csv(cls, rects, categories, point_in_category, output_csv_path="rects_for_input.csv"):
        """rects に category を追加して CSV に保存"""
        for r in rects:
            cats = [cat.name for cat in categories if point_in_category(r.center, cat)]
            r.category = ", ".join(cats) if cats else ""

        # CSV 出力
        with open(output_csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["no", "name", "power", "classification", "category", "tent", "light"])
            writer.writeheader()
            for r in rects:
                # --- nameから改行を削除（どんな改行でも全部削除）---
                clean_name = (
                    r.name
                    .replace("\r\n", "")   # Windowsの改行
                    .replace("\n", "")     # Unixの改行
                    .replace("\\n", "")    # 文字列上の "\n"
                )
                writer.writerow({
                    "no": getattr(r, "no", ""),
                    "name": clean_name,
                    "power": getattr(r, "power", ""),
                    "classification": getattr(r, "classification", ""),
                    "category": getattr(r, "category", ""),
                    "tent": getattr(r, "tent", ""),
                    "light": getattr(r, "light", ""),
                })

        print(f"Saved CSV -> {output_csv_path}")


    def draw_rects(self, screen, font, is_active=False, name_pos_active=False, tent_highlight=False):
        dirty = []

        # --- rect の色決定 ---
        comp_color = (255 - self.color[0], 255 - self.color[1], 255 - self.color[2])
        if name_pos_active:
            rect_color = self.color   # 通常 → 元の色
        elif is_active:
            rect_color = comp_color  # 四角アクティブ → 補色
        else:
            rect_color = self.color   # 通常 → 元の色

        # --- 四角形画像キャッシュ ---
        angle_changed = (self.angle != self._cache_rect_angle)
        size_changed = (self.size != getattr(self, "_cache_size", None))
        prev = getattr(self, "_cache_rect_color", None)
        color_changed = (rect_color != prev)

        if self._cache_rect_img is None or angle_changed or size_changed or color_changed:
            base = pygame.Surface(self.size, pygame.SRCALPHA)
            base.fill(rect_color)
            rotated = pygame.transform.rotate(base, -self.angle)
            
            self._cache_rect_img = rotated
            self._cache_rect_angle = self.angle
            self._cache_size = self.size
            self._cache_rect_color = rect_color

        rect = self._cache_rect_img.get_rect(center=self.center)
        screen.blit(self._cache_rect_img, rect)
        dirty.append(rect)
        self._last_rect = rect


        # --- No テキストは毎フレームでOK（軽量） ---
        brightness = sum(self.color)/3
        no_color = (0,0,0) if brightness > 128 else (255,255,255)

        # no_font = pygame.font.Font(font_path, int(self.size[1] * 0.75))
        # no_text = no_font.render(str(self.no), True, no_color)

        # --- No フォントキャッシュ ---
        no_font_size = int(self.size[1] * 0.75)

        if (
            not hasattr(self, "_cache_no_font")
            or self._cache_no_font is None
            or self._cache_no_font_size != no_font_size
        ):
            self._cache_no_font = pygame.font.Font(font_path, no_font_size)
            self._cache_no_font_size = no_font_size

        no_text = self._cache_no_font.render(str(self.no), True, no_color)

        no_text_rect = no_text.get_rect(center=self.center)
        screen.blit(no_text, no_text_rect)
        dirty.append(no_text_rect)


        # --- 名前ブロック画像キャッシュ ---
        name_changed = (
            self.name != getattr(self, "_cache_name_txt", None)
            or self.font_size != getattr(self, "_cache_font_size", None)
            or name_pos_active != getattr(self, "_cache_name_pos_active", None)
            or self.name_angle != self._cache_name_angle
        )

        # 色設定
        if is_active and name_pos_active:
            name_color = (0, 0, 255) # →青
        else:
            name_color = self.name_color

        # --- 名前テキスト画像キャッシュ判定 ---
        name_changed = (
            self._cache_name_img is None
            or name_color != getattr(self, "_cache_name_color", None)
            or self.name != getattr(self, "_cache_name_text", None)
            or self.font_size != getattr(self, "_cache_name_font_size", None)
            or name_pos_active != getattr(self, "_cache_name_pos_active", None)
        )

        # 生成
        # if name_changed:
        #     name_font = pygame.font.Font(font_path, self.font_size)
        #     name_str = self.name.replace("\\n", "\n")
        #     lines = name_str.split("\n")
        #     surfaces = [name_font.render(line, True, name_color) for line in lines]
        if name_changed:
            # --- name フォントキャッシュ ---
            if (
                not hasattr(self, "_cache_name_font")
                or self._cache_name_font is None
                or self._cache_name_font_size != self.font_size
            ):
                self._cache_name_font = pygame.font.Font(font_path, self.font_size)
                self._cache_name_font_size = self.font_size

            name_font = self._cache_name_font

            name_str = self.name.replace("\\n", "\n")
            lines = name_str.split("\n")
            surfaces = [name_font.render(line, True, name_color) for line in lines]

            line_spacing = int(self.font_size * -0.5)
            w = max(s.get_width() for s in surfaces)
            h = sum(s.get_height() for s in surfaces) + line_spacing * (len(lines)-1)

            block = pygame.Surface((w, h), pygame.SRCALPHA)
            y = 0
            for s in surfaces:
                block.blit(s, (0, y))
                y += s.get_height() + line_spacing

            rotated_block = pygame.transform.rotate(block, self.name_angle)

            self._cache_name_img = rotated_block
            self._cache_name_txt = self.name
            self._cache_font_size = self.font_size
            self._cache_name_angle = self.name_angle
            self._cache_name_pos_active = name_pos_active


        if getattr(self, "_cache_name_img", None):
            block_rect = self._cache_name_img.get_rect(
                topleft=(self.center[0] + self.name_pos[0], self.center[1] + self.name_pos[1])
            )
            screen.blit(self._cache_name_img, block_rect)
            dirty.append(block_rect)
            self._last_name_rect = block_rect

        # --- テント枠描画（tent > is_active > 通常） ---
        if getattr(self, "tent", 0) and int(self.tent) > 0 and tent_highlight:
            outline_color = (255, 0, 0)
            outline_width = 3
        elif is_active:
            outline_color = (80, 80, 80)
            outline_width = 2
        else:
            outline_color = (0, 0, 0)
            outline_width = 1

        # --- 回転枠描画 ---
        if outline_color is not None:
            # 回転前サイズを保持している前提
            size = self.size            # (w, h)
            angle = self.angle          # degree
            center = rect.center        # blit後の中心

            points = get_rotated_rect_points(center, size, angle)

            pygame.draw.polygon(
                screen,
                outline_color,
                points,
                outline_width
            )

            # dirty rect（AABBで十分）
            dirty.append(rect.copy())

        return dirty

    def is_highlighted(self):
        return int(self.tent) > 0

    def contains_point(self, p):
        """クリック判定"""
        if isinstance(self, RotatingRect):
            if hasattr(self, "_last_rect") and self._last_rect:
                return self._last_rect.collidepoint(p)
            else:
                dx = p[0] - self.center[0]
                dy = p[1] - self.center[1]
                return math.hypot(dx,dy) < max(self.size)*1.0

    def get_categories(self, categories, point_in_category):
        """
        Rect が属するカテゴリ名リストを返す（キャッシュあり）
        """
        if self._cache_center == self.center:
            return self._cache_categories

        cats = [
            cat.name
            for cat in categories
            if not cat.alert and point_in_category(self.center, cat)
        ]

        self._cache_center = self.center
        self._cache_categories = cats
        return cats

    def move(self, dx, dy):
        self.center = (self.center[0] + dx, self.center[1] + dy)
        self._cache_categories = None
        self._cache_center = None

    def draw_view_only(
            screen,
            rects,
            font_cache,
            tent_highlight=True,
            dirty=None,
        ):
        """
        編集不可の view 用描画
        draw_rects と同一の見た目
        """
        def draw_rotated_rect_outline(screen, center, size, angle, color, width):
            """回転矩形の枠のみ描画"""
            w, h = size
            hw, hh = w / 2, h / 2

            # 未回転の4点
            points = [
                (-hw, -hh),
                ( hw, -hh),
                ( hw,  hh),
                (-hw,  hh),
            ]

            rad = math.radians(angle)
            cos_a = math.cos(rad)
            sin_a = math.sin(rad)

            rotated = []
            for x, y in points:
                rx = x * cos_a - y * sin_a + center[0]
                ry = x * sin_a + y * cos_a + center[1]
                rotated.append((rx, ry))

            pygame.draw.polygon(screen, color, rotated, width)
            return pygame.Rect(min(p[0] for p in rotated),
                            min(p[1] for p in rotated),
                            max(p[0] for p in rotated) - min(p[0] for p in rotated),
                            max(p[1] for p in rotated) - min(p[1] for p in rotated))

        if dirty is None:
            dirty = []

        for r in rects:
            # --- 本体描画（回転） ---
            surf = pygame.Surface(r.size, pygame.SRCALPHA)
            surf.fill(r.color)
            rot_surf = pygame.transform.rotate(surf, -r.angle)
            rect = rot_surf.get_rect(center=r.center)
            screen.blit(rot_surf, rect)
            dirty.append(rect)

            # --- 枠線条件（draw_rects と同じ） ---
            if getattr(r, "tent", 0) and int(r.tent) > 0 and tent_highlight:
                outline_color = (255, 0, 0)
                outline_width = 3
            else:
                outline_color = (0, 0, 0)
                outline_width = 1

            # --- 回転枠描画 ---
            outline_rect = draw_rotated_rect_outline(
                screen,
                r.center,
                r.size,
                r.angle,
                outline_color,
                outline_width
            )
            dirty.append(outline_rect)

            # --- 名前描画 ---
            if r.name:
                key = (r.font_size, r.name, r.name_color)
                if key not in font_cache:
                    font = pygame.font.SysFont(None, r.font_size)
                    font_cache[key] = font.render(r.name, True, r.name_color)

                name_surf = font_cache[key]
                if r.name_angle != 0:
                    name_surf = pygame.transform.rotate(name_surf, -r.name_angle)

                name_rect = name_surf.get_rect(
                    center=(r.center[0] + r.name_pos[0],
                            r.center[1] + r.name_pos[1])
                )
                screen.blit(name_surf, name_rect)
                dirty.append(name_rect)

        return dirty

# -----------------------------
# ポリゴンクラス（マップ上オブジェクト）
# -----------------------------
class PolygonShape:
    def __init__(
        self,
        points=[(100,200), (200,100)],
        color=(150, 200, 250),
        width=3,
        show_vertices=True,
    ):
        self.points = list(points)        # [(x, y), ...]
        self.color = tuple(color)
        self.width = width
        self.show_vertices = show_vertices
        self.active = False
        self.active_vertex = False
        self.dragging = None
        self.dragging_vertex = None
        self.drag_offset = (0, 0)
        self.vertex_drag_offset = (0, 0)
        self.classification = "polygon"

        self.visible = True
        self.prev_dirty = []

    def to_dict(self):
        """JSON保存用"""
        return {
            "points": [list(p) for p in self.points],
            "color": list(self.color),
            "width": self.width,
            "show_vertices": self.show_vertices,
        }

    @classmethod
    def from_dict(cls, d):
        """JSON読み込み用"""
        return cls(
            points=[tuple(p) for p in d.get("points", [])],
            color=tuple(d.get("color", (150, 200, 250))),
            width=d.get("width", 3),
            show_vertices=d.get("show_vertices", True),
        )

    def contains_line(self, pos, tolerance=6):
        """辺クリック判定（ポリゴン）"""
        if len(self.points) < 2:
            return False

        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % len(self.points)]
            if point_to_segment_distance(pos, p1, p2) <= tolerance:
                return True

        return False
    
    def draw_polygon(
        self,
        draw_surface,
        is_active=False,
        active_vertex=None,
        selected_vertex=None,
        show_vertices=None,
        show_vertex_index=False,
    ):
        if not self.visible or not self.points:
            return []

        if show_vertices is None:
            show_vertices = self.show_vertices

        dirty = []

        # --- 描画範囲算出 ---
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        pad = 10
        area = pygame.Rect(
            min_x - pad,
            min_y - pad,
            (max_x - min_x) + pad * 2,
            (max_y - min_y) + pad * 2
        )

        # --- 本体 ---
        col = (255, 100, 100) if is_active else self.color
        pygame.draw.lines(
            draw_surface,
            col,
            False,
            self.points,
            self.width
        )

        # --- 頂点描画 ---
        if show_vertices and is_active:
            selected_vi = None
            if selected_vertex:
                pi, selected_vi = selected_vertex

            for i, (x, y) in enumerate(self.points):
                # 色決定
                if selected_vi is not None and i == selected_vi:
                    color = (255, 0, 0)  # 選択頂点：赤
                else:
                    color = (0, 0, 255)  # 通常頂点：青

                pygame.draw.circle(
                    draw_surface,
                    color,
                    (int(x), int(y)),
                    6
                )
                    

        # --- active 時の頂点番号 ---
        if is_active and show_vertex_index:
            for i, (x, y) in enumerate(self.points):
                no_surf = font_path.render(str(i), True, (0, 0, 0))
                rect = no_surf.get_rect(center=(x, y - 12))
                draw_surface.blit(no_surf, rect)
                dirty.append(rect)

        dirty.append(area)
        return dirty


    def contains_line(self, pos, tolerance=6):
        """辺クリック判定（ポリゴン）"""
        if len(self.points) < 2:
            return False

        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % len(self.points)]
            if point_to_segment_distance(pos, p1, p2) <= tolerance:
                return True

        return False


#-----------------------
# 新規オブジェクト追加関数 右クリックウィンドウからの追加用
#-----------------------
def add_rect(rects, active, pos, screen, context_menu=False):
    name = f"Rect{len(rects)+1}"

    if active is None:
        if not context_menu:
            new = RotatingRect(
                name=name,
                center=(SCREEN_W//2, SCREEN_H//2),
                size=(25, 25)
            )
        if context_menu:
            mx, my = convert_mouse_to_draw_coords(pos, screen)

            new = RotatingRect(
                name=name,
                center=(mx, my),
                size=(25, 25),
            )
    else:
        new = RotatingRect(
            name=name,
            center=pos,
            size=active.size,
            angle=active.angle,
            name_pos=active.name_pos,
            name_angle=active.name_angle,
            classification=active.classification,
            color=active.color,
            font_size=active.font_size,
        )

    new.name_pos_active = False
    return new

def add_polygon(polygons, active, pos, screen, context_menu=False):
    name = f"Polygon{len(polygons)+1}"

    mx, my = convert_mouse_to_draw_coords(pos, screen)

    if active is None:
        points = [(mx, my), (mx+100, my+100)]

    new = PolygonShape(
        points=points,
        color=(0,0,0),
        width=2,
    )

    return new