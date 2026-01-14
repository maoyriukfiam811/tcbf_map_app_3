import os
import math
import pygame
import tkinter as tk
import json, csv
import config
from tkinter import ttk, simpledialog, filedialog, messagebox
from config import DRAW_W, DRAW_H, SCREEN_W, SCREEN_H


def convert_mouse_to_draw_coords(pos, screen):
    """マウス座標を描画用座標に変換"""
    sw, sh = screen.get_size()
    scale_x = config.DRAW_W / sw
    scale_y = config.DRAW_H / sh

    mx, my = pos
    mx *= scale_x
    my *= scale_y

    return mx, my

# -----------------------------
# ユーティリティ関数
# -----------------------------
def point_in_category(pt, cat):
    """点(pt)がカテゴリ(cat)内にあるか判定"""
    if cat.points:
        pts = cat.points
        n = len(pts)
        inside = False
        px, py = pt
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if ((y1 > py) != (y2 > py)) and \
               (px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-9) + x1):
                inside = not inside
        return inside
    return False

def categories_name_containing_rect(center, categories):
    """矩形(rect)がカテゴリ(cat)内にあるか判定"""
    category_list = []
    for cat in categories:
        if point_in_category(center, cat):
            category_list.append(cat.name)
    return category_list

def drag_object(obj, mouse_pos, screen, SCREEN_W, SCREEN_H):
    """ドラッグ中オブジェクト（Rect/Text）を移動させる共通関数"""
    if not getattr(obj, "dragging", False):
        return

    # sw, sh = screen.get_size()
    # scale_x = DRAW_W / sw
    # scale_y = DRAW_H / sh

    # mx, my = mouse_pos
    # mx *= scale_x
    # my *= scale_y

    mx, my = convert_mouse_to_draw_coords(mouse_pos, screen)

    ox, oy = obj.drag_offset

    nx = max(0, min(SCREEN_W, mx + ox))
    ny = max(0, min(SCREEN_H, my + oy))

    # Rect も Text も "中心" と "位置" の違いがあるので分岐
    if hasattr(obj, "center") and hasattr(obj, "move"):
        # if hasattr(obj, "center"):
        #     obj.center = (nx, ny)
        dx = nx - obj.center[0]
        dy = ny - obj.center[1]
        if dx or dy:
            obj.move(dx, dy)

    elif hasattr(obj, "position"):
        obj.position = (nx, ny)
    elif hasattr(obj, "points"):
        obj.points = (nx, ny)

def rotate_angle(target, delta):
    """対象オブジェクトの角度を delta 分だけ回転させる"""
    target.angle = (target.angle + delta) % 360

def undo_delete_object(objs):
    """直前に削除したオブジェクトを復元し、復元したobj(activeにする)を返す"""
    d_obj = config.last_deleted_obj
    if d_obj is not None:
        objs.append(d_obj)        
        config.last_deleted_obj = None
        for obj in objs:
            if obj is d_obj:
                active = obj
                return active
    elif d_obj is None:
        None

def delete_object(obj, objs):
    """対象オブジェクトをリストから削除する"""
    if obj in objs:
        config.last_deleted_obj = obj
        objs.pop(objs.index(obj))
        obj = None
    else:
        print(f"deleted: 'None'")
        None

# -----------------------------
# PNG保存
# -----------------------------
def save_as_png(draw_surface):
    """PNG保存ダイアログを開いてPNG保存を行う"""
    try:
        file_path = filedialog.asksaveasfilename(
            title="PNGとして保存",
            defaultextension=".png",
            filetypes=[("PNG画像", "*.png"), ("すべてのファイル", "*.*")]
        )

        if not file_path:
            return  # キャンセル

        pygame.image.save(draw_surface, file_path)
        print(f"Saved PNG (1920x1080) -> {file_path}")

    except Exception as e:
        print("PNG保存エラー:", e)
        messagebox.showerror("保存エラー", f"PNGの保存に失敗しました:\n{e}")
        

# -----------------------------
# キー押下による頂点移動（スナップ対応）
# -----------------------------
def handle_key_movement(now, last_move_time, move_delay, keys, prev_keys, ctrl, shift, x, y, step=5, w=SCREEN_W, h=SCREEN_H, allow_negative=False):
    """矢印キーで移動。Ctrl=50スナップ、Shift=10スナップ、通常ステップも適用"""
    for key, dx, dy in [
        (pygame.K_LEFT, -1, 0),
        (pygame.K_RIGHT, 1, 0),
        (pygame.K_UP, 0, -1),
        (pygame.K_DOWN, 0, 1)
    ]:
        pressed = keys[key]
        was_pressed = prev_keys[key]
        pressed_now = pressed and not was_pressed  # 押した瞬間

        move = pressed_now or (pressed and (now - last_move_time >= move_delay))

        if move:
            # --- 移動量を決定 ---
            if ctrl:
                delta = 50
            elif shift:
                delta = 10
            else:
                delta = step

            if key in [pygame.K_LEFT, pygame.K_RIGHT]:
                x += dx * delta
                x = round(x / delta) * delta
            else:
                y += dy * delta
                y = round(y / delta) * delta

            # --- 範囲制限 ---
            if not allow_negative:
                x = max(0, min(w, x))
                y = max(0, min(h, y))

            last_move_time = now

    return x, y, last_move_time


def move_active_rects(active, active_rects, now, last_move_time, move_delay, keys, prev_keys, ctrl, shift, screen_w, screen_h):
    """単体または複数選択オブジェクトを移動させる"""
    # --- 複数選択 ---
    if active_rects:
        base = active_rects[0]   # 代表
        x0, y0 = base.center

        # まず代表オブジェクトだけ handle_key_movement に通す
        x_new, y_new, last_move_time = handle_key_movement(now, last_move_time, move_delay, keys, prev_keys, ctrl, shift, x0, y0, w=screen_w, h=screen_h)

        # 移動量（dx, dy）
        dx = x_new - x0
        dy = y_new - y0

        # 全メンバーに同じ移動量を適用
        for r in active_rects:
            rx, ry = r.center
            r.center = (rx + dx, ry + dy)

        return last_move_time

    # --- 単体選択 ---
    if active:
        x, y = active.center
        x, y, last_move_time = handle_key_movement(
            now, last_move_time, move_delay,
            keys, prev_keys, ctrl, shift,
            x, y, w=screen_w, h=screen_h
        )
        active.center = (x, y)

    return last_move_time



# -----------------------------
# 背景画像選択ダイアログ
# -----------------------------
BG_FILE = "BG_FILE.json"

# 背景画像パス保存/読込
def select_background_file():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="背景画像を選択",
        filetypes=[
            ("画像ファイル", "*.png;*.jpg;*.jpeg;*.bmp"),
            ("すべてのファイル", "*.*")
        ]
    )

    root.destroy()

    if file_path:
        # BG_FILE.json が無ければここで作成（あっても上書き）
        save_bg_path(file_path)
        return file_path

    return None

def load_bg_path():
    if os.path.exists(BG_FILE):
        with open(BG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("path", None)
    return None

def save_bg_path(path):
    with open(BG_FILE, "w", encoding="utf-8") as f:
        json.dump({"path": path}, f, ensure_ascii=False, indent=2)

def load_and_resize_bg(bg_image_path):
    try:
        print("Loading background:", bg_image_path)
        img = pygame.image.load(bg_image_path).convert_alpha()  # ← ここを追加
        iw, ih = img.get_size()
        sw, sh = DRAW_W, DRAW_H
        scale = min(sw / iw, sh / ih)
        new_size = (int(iw * scale), int(ih * scale))
        img = pygame.transform.smoothscale(img, new_size)
        surface = pygame.Surface((sw, sh), pygame.SRCALPHA)
        surface.fill((255, 255, 255, 255))  # 背景色を不透明にしたい場合は (255,255,255)
        surface.blit(img, ((sw - new_size[0]) // 2, (sh - new_size[1]) // 2))
        return surface
    except Exception as e:
        print("背景画像読み込みエラー:", e)
        return None

def draw_background(screen, bg_image):
    if bg_image:
        screen.blit(bg_image, (0,0))
    else:
        screen.fill((250,250,255))


# -----------------
# category_mode用
# -----------------
def get_active_polygon_index(pt, polygons):
    """
    クリック点 pt が含まれるカテゴリのインデックスを返す
    先に見つかったカテゴリを返す（重なり時は上のカテゴリ優先）
    """
    for i, cat in enumerate(polygons):
        if point_in_category(pt, cat):
            return i  # カテゴリのインデックスを返す
    return None

def get_active_point_index(pt, polygons, radius=10):
    """
    クリック点 pt が近い頂点のインデックスを返す。
    先に見つかった頂点を返す（重なり時は上のカテゴリ・上の頂点優先）。
    
    戻り値:
        (si, vi) または None
    """
    px, py = pt
    for si, cat in enumerate(polygons):
        for vi, (vx, vy) in enumerate(cat.points):
            dx = px - vx
            dy = py - vy
            if dx*dx + dy*dy <= radius**2:
                return (si, vi)
    return None


def handle_vertex_movement(x, y, now, last_move_time, move_delay, keys, prev_keys, ctrl, shift, step=5, w=SCREEN_W, h=SCREEN_H):

    # 速度調整
    if ctrl:
        step = 50
    if shift:
        step = 10

    moved = False
    dx = dy = 0

    # 押された瞬間 または 一定時間ごとに入力を受け付ける
    allow = False

    # 押された瞬間
    for k in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
        if keys[k] and not prev_keys[k]:
            allow = True

    # 押しっぱなし連続入力
    if now - last_move_time >= move_delay:
        allow = True

    if allow:
        if keys[pygame.K_UP]:
            dy -= step
            moved = True
        if keys[pygame.K_DOWN]:
            dy += step
            moved = True
        if keys[pygame.K_LEFT]:
            dx -= step
            moved = True
        if keys[pygame.K_RIGHT]:
            dx += step
            moved = True

        if moved:
            last_move_time = now

    # --- 移動 ---
    nx = min(max(x + dx, 0), w)
    ny = min(max(y + dy, 0), h)

    # --- スナップ（座標をきれいに揃える） ---
    nx = round(nx / step) * step
    ny = round(ny / step) * step

    return dx, dy, nx, ny, last_move_time


def handle_category_movement(category, now, last_move_time, move_delay,
                      keys, prev_keys, ctrl, shift, step=5,
                      SCREEN_W=SCREEN_W, SCREEN_H=SCREEN_H):
    """
    キー操作でカテゴリ全体を移動する。
    基準点は points[0]。
    """

    if not category.points:
        return last_move_time

    # 基準点
    base_x, base_y = category.points[0]

    # move_vertex_keyで基準点を移動
    dx, dy, new_x, new_y, last_move_time = handle_vertex_movement(
        base_x, base_y, now, last_move_time, move_delay,
        keys, prev_keys, ctrl, shift, step, SCREEN_W, SCREEN_H
    )

    # dx/dyを全頂点に適用
    category.points = [(x + dx, y + dy) for x, y in category.points]

    return last_move_time


def drag_category_or_polygon(category, mouse_pos, screen, DRAW_W, DRAW_H, SCREEN_W, SCREEN_H, offset):
    """
    カテゴリ多角形全体のドラッグ移動量(dx, dy)を返す。
    """
    if not category.points:
        return 0, 0

    if offset is None:
        return 0, 0

    ox, oy = offset
    x0, y0 = category.points[0]

    sw, sh = screen.get_size()
    scale_x = DRAW_W / sw
    scale_y = DRAW_H / sh

    mx, my = mouse_pos
    mx *= scale_x
    my *= scale_y

    nx = max(0, min(SCREEN_W, mx + ox))
    ny = max(0, min(SCREEN_H, my + oy))

    dx = nx - x0
    dy = ny - y0

    return dx, dy

def drag_vertex(polygon, vi, mouse_pos, screen, DRAW_W, DRAW_H, SCREEN_W, SCREEN_H, offset):
    """
    単一頂点のドラッグ移動量(dx, dy)を返す。
    convert_mouse_to_draw_coords を使わず、drag_object と同じ変換方式。
    """

    if not polygon.points:
        return 0, 0

    ox, oy = offset
    # --- 現在の頂点座標 ---
    x0, y0 = polygon.points[vi]

    # --- 画面→内部座標変換（drag_object と同じ） ---
    sw, sh = screen.get_size()
    scale_x = DRAW_W / sw
    scale_y = DRAW_H / sh

    mx, my = mouse_pos
    mx *= scale_x
    my *= scale_y

    # --- 新しい位置 ---
    nx = max(0, min(SCREEN_W, mx + ox))
    ny = max(0, min(SCREEN_H, my + oy))

    # --- 移動量 ---
    dx = nx - x0
    dy = ny - y0

    return dx, dy


def screen_to_internal(pos, screen_size, draw_size):
    """
    pos         : (screen_x, screen_y)
    screen_size : (window_w, window_h)
    draw_size   : (DRAW_W, DRAW_H)

    return (internal_x, internal_y)
    """
    sx, sy = pos
    window_w, window_h = screen_size
    draw_w, draw_h = draw_size

    scale = min(window_w / draw_w, window_h / draw_h)
    offset_x = (window_w - draw_w * scale) // 2
    offset_y = (window_h - draw_h * scale) // 2

    ix = (sx - offset_x) / scale
    iy = (sy - offset_y) / scale

    return ix, iy

def calc_vertex_drag_offset(vertex_pos, mouse_pos_internal):
    """
    vertex_pos        : (vx, vy)
    mouse_pos_internal: (ix, iy)
    """
    vx, vy = vertex_pos
    ix, iy = mouse_pos_internal
    return vx - ix, vy - iy

def calc_category_or_polygon_drag_offset(category, mouse_pos_internal):
    """
    category : CategoryShape
    """
    x0, y0 = category.points[0]
    ix, iy = mouse_pos_internal
    return x0 - ix, y0 - iy


# -----------------
# マップモード用
# -----------------
JSON_FILE = "JSON_FILE.json"

def select_json_file():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="JSONファイルを選択",
        filetypes=[
            ("JSONファイル", "*.json"),
            ("すべてのファイル", "*.*")
        ]
    )

    root.destroy()

    # if file_path:
    save_json_path(file_path)
    return file_path

    # return None

def load_json_path():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("path")
    return None

def save_json_path(path):
    print("Saving JSON path:", path)
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump({"path": path}, f, ensure_ascii=False, indent=2)


def categories_power_list(rects, categories, point_in_category):
    """
    Rects, Categoriesから総電力リストを返す
    """
    power_totals = {}
    no_cat_total = 0
    total_power = 0

    # --- カテゴリ一覧を rect 非依存で確定 ---
    unique = {}
    for cc in categories:
        if getattr(cc, "alert", False):
            continue
        key = (cc.name, cc.power_limit)
        if key not in unique:
            unique[key] = cc

    sorted_categories = sorted(unique.values(), key=lambda cc: cc.name)

    # --- 初期値として 0 を入れておく（重要） ---
    for cc in sorted_categories:
        power_totals[cc.name] = 0

    # --- rect 処理 ---
    for r in rects:
        try:
            r_power = int(r.power)
        except (ValueError, TypeError):
            r_power = 0

        total_power += r_power

        cats = r.get_categories(sorted_categories, point_in_category)

        if not cats:
            no_cat_total += r_power
        else:
            for cat_name in cats:
                power_totals[cat_name] += r_power

    return power_totals, sorted_categories


def get_rotated_rect_points(center, size, angle_deg):
    """
    center : (cx, cy)
    size   : (w, h)
    angle_deg : 回転角（度）
    戻り値 : [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
    """
    cx, cy = center
    w, h = size
    angle = math.radians(angle_deg)

    hw, hh = w / 2, h / 2

    # 回転前の4頂点（左上から時計回り）
    corners = [
        (-hw, -hh),
        ( hw, -hh),
        ( hw,  hh),
        (-hw,  hh),
    ]

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    rotated = []
    for x, y in corners:
        rx = x * cos_a - y * sin_a + cx
        ry = x * sin_a + y * cos_a + cy
        rotated.append((rx, ry))

    return rotated


def count_total_by_classification(rects):
    counts = {}

    if not rects:
        return counts

    for r in rects:
        key = getattr(r, "classification", None)
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1

    return counts

import math

def point_to_segment_distance(p, a, b):
    """
    polygon用
    p : (x, y) 判定点
    a : (x, y) 線分始点
    b : (x, y) 線分終点
    return : 最短距離
    """
    px, py = p
    ax, ay = a
    bx, by = b

    dx = bx - ax
    dy = by - ay

    if dx == 0 and dy == 0:
        # a == b（点）
        return math.hypot(px - ax, py - ay)

    # 射影パラメータ t
    t = ((px - ax) * dx + (py - ay) * dy) / (dx*dx + dy*dy)
    t = max(0, min(1, t))

    closest_x = ax + t * dx
    closest_y = ay + t * dy

    return math.hypot(px - closest_x, py - closest_y)

def hit_test_polyline(pos, points, tolerance=6):
    """
    pos       : マウス位置
    points    : [(x,y), (x,y), ...]
    tolerance : 判定半径（px）
    """
    if len(points) < 2:
        return False

    for i in range(len(points) - 1):
        if point_to_segment_distance(pos, points[i], points[i+1]) <= tolerance:
            return True

    return False
