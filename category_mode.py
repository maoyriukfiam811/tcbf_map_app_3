import pygame
import tkinter as tk
from tkinter import simpledialog
from utils import (draw_background, load_and_resize_bg, load_bg_path, point_in_category, 
                   get_active_point_index, get_active_polygon_index, drag_vertex, drag_category_or_polygon, handle_category_movement, handle_vertex_movement,
                   screen_to_internal, calc_vertex_drag_offset, calc_category_or_polygon_drag_offset)
from objects import CategoryShape, DataManager
from config import font_path, SCREEN_W, SCREEN_H
from object_editor import confirm_quit, edit_category_dialog

# -----------------------------
# ルール
# -----------------------------
# ci: categoryのリスト番号
# vi: vertex(points)のリスト番号
# ci, vi = selected_vertex
# x, y = categories[ci].points[vi]

# -----------------------------
# カテゴリ編集モード
# -----------------------------
def run_category_editor(screen, font, rects, texts, categories, polygons, filename):
    """カテゴリ編集モード"""
    import tkinter as tk
    # root = tk.Tk()
    # root.withdraw()

    DRAW_W, DRAW_H = 1920, 1080  # 内部描画解像度（固定）
    draw_surface = pygame.Surface((DRAW_W, DRAW_H))  # 内部用Surface

    # rects, texts, categories, filename = DataManager.load_all()
    pygame.display.set_caption(f"{filename}")

    clock = pygame.time.Clock()
    selected_vertex = None
    selected_cat = None
    cat = None
    dragging = False
    move_delay = 0.15
    last_move_time = 0
    ime_warned_message_until = 0
    prev_keys = pygame.key.get_pressed()
    last_deleted_cat = None
    vertex_drag_offset = None  # 選択頂点用
    category_drag_offset = None  # 選択カテゴリ用
    font_small = pygame.font.Font(font_path, 15)
    save_message_until = 0

    running = True

    bg_image_path = load_bg_path()
    bg_image = load_and_resize_bg(bg_image_path) if bg_image_path else None

    while running:
        # ---- 内部Surfaceにすべて描画 ----
        draw_background(draw_surface, bg_image=bg_image)

        now = pygame.time.get_ticks() / 1000.0

        # カテゴリ描画（選択頂点・名前・頂点表示あり）
        for i, c in enumerate(categories):
            av = None
            if selected_vertex is not None and i == selected_vertex[0]:
                av = selected_vertex[1]
            c.draw_category(draw_surface, font, active=(i==selected_cat), active_vertex=av, show_names=True, show_vertices=True)

        # IME ON(日本語入力時)警告
        if now < ime_warned_message_until:
            msg_surf = font.render("IME ON/日本語 -> IME OFF/アルファベット", True, (0, 0, 0))
            draw_surface.blit(msg_surf, (DRAW_W - msg_surf.get_width() - 10, 10))

        # ---電力上限表記---
        # (name, power) で重複排除
        unique = {}
        for c in categories:
            if getattr(c, "alert", False):
                continue  # alert対象は表示しない
            key = (c.name, c.power_limit)
            if key not in unique:
                unique[key] = c
        # name で並び替え
        sorted_categories = sorted(unique.values(), key=lambda c: c.name)
        # 描画
        base_y = 110
        for i, c in enumerate(sorted_categories):
            y = base_y + i * 20
            text = f"name: {c.name}  power_limit: {c.power_limit}"
            surf = font_small.render(text, True, (0, 0, 0))
            draw_surface.blit(surf, (10, y))

        # 操作説明
        instructions = [
            "クリック: オブジェクト選択",
            "ドラッグ、矢印キー: オブジェクト移動",
            "空白クリック/ESC: 選択解除",
            "Shift+矢印キー: 10px移動",
            "Ctrl+矢印キー: 50px移動",
            "N: オブジェクト追加",
            "Enter(アクティブ中): カテゴリ名/色/*アラート編集",
            "*アラート: テントなどを配置できない場所を設定",
            "(Shift+)Tab: カテゴリ変更/カテゴリ選択(逆順)",
            "Space(アクティブ中): ポイントアクティブ化",
            "Ctrl+S: 保存",
            "ESC: 保存して戻る",
            "Ctrl+Z: 元に戻す（削除のみ）",
        ]

        # --- 操作説明描画（左下配置） ---
        y_offset = DRAW_H - 20 * len(instructions) - 10  # 下端から上にずらす
        x_offset = 10  # 左端から10px
        for i, line in enumerate(instructions):
            text_surf = font_small.render(line, True, (0, 0, 0))
            draw_surface.blit(text_surf, (x_offset, y_offset + i * 20))

        # --- アクティブオブジェクト情報表示 ---
        if selected_cat: #単一選択
            # category が1つもない
            if not categories:
                return

            # selected_cat 補正
            if selected_cat < 0:
                selected_cat = 0
            elif selected_cat >= len(categories):
                selected_cat = len(categories) - 1

            pts = categories[selected_cat].points

            # point がない場合は描画スキップ
            if not pts:
                return

            # vi 補正
            ci = vi = None
            if selected_vertex is not None:
                ci, vi = selected_vertex

            # vi を使う処理を安全に
            if vi is not None:
                if vi < 0:
                    vi = 0
                if vi >= len(categories[ci].points):
                    vi = len(categories[ci].points) - 1


            draw_surface.blit(font_small.render(f"name: {categories[selected_cat].name}", True, (0,0,0)), (10, 50)) #1行目
            draw_surface.blit(font_small.render(f"point: {categories[selected_cat].points[vi]}", True, (0,0,0)), (10, 70)) #2行目以降
        else:
            None

        # Ctrl+S save message
        if now < save_message_until:
            msg_surf = font.render("Saved all objects.", True, (0, 0, 0))
            draw_surface.blit(msg_surf, (DRAW_W - msg_surf.get_width() - 10, 10))

        pygame.display.flip()
        keys = pygame.key.get_pressed()
        mods = pygame.key.get_mods()
        ctrl = mods & pygame.KMOD_CTRL
        shift = mods & pygame.KMOD_SHIFT

        if selected_vertex is not None:
            ci, vi = selected_vertex
            x, y = categories[int(ci)].points[int(vi)]
            dx, dy, new_x, new_y, last_move_time = handle_vertex_movement(
                x, y, now, last_move_time, move_delay,
                keys, prev_keys, ctrl, shift, step=5, w=SCREEN_W, h=SCREEN_H)
            categories[ci].points[vi] = (new_x, new_y)

        elif selected_cat is not None:
            last_move_time = handle_category_movement(
                categories[selected_cat], now, last_move_time, move_delay,
                keys, prev_keys, ctrl, shift)
            
        prev_keys = keys

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if confirm_quit():
                    DataManager.save_all(rects, texts, categories, polygons, filename)
                    return "back_to_mode_select"
                else:
                    running = False
            # ウィンドウリサイズ処理
            elif event.type == pygame.VIDEORESIZE:
                bg_image = load_and_resize_bg(bg_image_path) if bg_image_path else None
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            # IME ON(日本語入力)
            # elif event.type == pygame.TEXTINPUT:
                # print("IME ON -> IME OFF.")
                # ime_warned_message_until = now + 3  # 今から3秒後
                # continue

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if selected_vertex is not None:
                        selected_vertex = None
                    elif selected_cat is not None:
                        selected_cat = None
                    else:
                        if confirm_quit():
                            DataManager.save_all(rects, texts, categories, polygons, filename)
                            return "back_to_mode_select"
                        else:
                            return "back_to_mode_select"

                if event.key == pygame.K_TAB:
                    if shift:  # 逆順切替
                        if selected_vertex is not None:
                            ci, vi = selected_vertex
                            cat = categories[ci]
                            vi = (vi - 1 + len(cat.points)) % len(cat.points)
                            selected_vertex = (ci, vi)
                        elif selected_cat is not None:  # カテゴリ選択中
                            selected_cat = (selected_cat - 1 + len(categories)) % len(categories)
                        else:  # カテゴリ未選択中
                            selected_cat = 0  # 先頭カテゴリを選択
                    else:  # 順方向切替
                        if selected_vertex is not None:
                            ci, vi = selected_vertex
                            cat = categories[ci]
                            vi = (vi + 1) % len(cat.points)
                            selected_vertex = (ci, vi)
                        elif selected_cat is not None:
                            selected_cat = (selected_cat + 1) % len(categories)
                        else:
                            selected_cat = 0  # 先頭カテゴリを選択

                # 新規ポリゴン追加（初期三角形）
                if event.key == pygame.K_n:
                    if selected_vertex is not None:
                        ci, vi = selected_vertex
                        cat = categories[ci]
                        # 安全チェック
                        if 0 <= vi < len(cat.points):
                            # 既存ポイントを複製（基本形）
                            x, y = cat.points[vi]
                            new_point = (x + 10, y + 10)
                            # new_point = cat.points[vi]
                            # vi+1 に挿入
                            cat.points.insert(vi + 1, new_point)
                            # 新しいポイントをアクティブに
                            selected_vertex = (ci, vi + 1)

                    elif selected_cat is not None and selected_vertex is None:
                        # ★選択中カテゴリの完全コピー（形をそのまま複製）
                        base_cat = categories[selected_cat]

                        # 座標を +20, +20 移動したコピー
                        pts = [(x + 20, y + 20) for (x, y) in base_cat.points]

                        categories.append(
                            CategoryShape(
                                name=f"cat_{len(categories)+1}",
                                color=categories[selected_cat].color,
                                points=pts,
                            )
                        )

                        selected_cat = len(categories) - 1
                        selected_vertex = None

                    elif selected_cat is None:
                        cx,cy = SCREEN_W//2, SCREEN_H//2
                        size = 80
                        pts = [
                            (cx - size//2, cy - size//2),  # 左上
                            (cx - size//2, cy + size//2),  # 左下
                            (cx + size//2, cy + size//2),  # 右下
                            (cx + size//2, cy - size//2),  # 右上
                        ]
                        
                        categories.append(
                            CategoryShape(
                                name=f"cat_{len(categories)+1}",
                                color=(150, 200, 250),
                                points=pts
                            )
                        )

                        selected_cat = len(categories) - 1
                        selected_vertex = None

                if selected_cat is not None and event.key == pygame.K_SPACE:
                    if selected_vertex is None:
                        ci = selected_cat
                        if categories[ci].points:
                            vi = 0
                            selected_vertex = (ci, vi)
                    elif selected_vertex is not None:
                        selected_vertex = None

                # 選択ポリゴン削除
                if selected_cat is not None and selected_vertex is None and event.key == pygame.K_DELETE:
                    if 0 <= selected_cat < len(categories):
                        # delete_unit(selected_cat, categories)
                        last_deleted_cat = categories[selected_cat]
                        categories.pop(selected_cat)
                        selected_cat = None
                        selected_vertex = None

                # UNDO
                if ctrl and event.key == pygame.K_z:
                    if last_deleted_cat is not None:
                        categories.append(last_deleted_cat)
                        last_deleted_cat = None # 1回だけ戻せる
                        selected_cat = None

                # SAVE
                if ctrl and event.key == pygame.K_s:
                    DataManager.save_all(rects, texts, categories, polygons, filename)
                    save_message_until = now + 3  # 今から3秒後

                # 選択頂点削除
                if selected_vertex is not None and event.key == pygame.K_d:
                    ci, vi = selected_vertex
                    cat = categories[ci]

                    if len(cat.points) > 3:
                        cat.points.pop(vi)

                        # vi を必ず補正して selected_vertex を整数indexペアに戻す
                        new_vi = min(vi, len(cat.points) - 1)
                        selected_vertex = (ci, new_vi)

                    else:
                        print("3点以下のため削除できません")
                        

                # エンターキーで名前変更/アラート有無変更
                if selected_cat is not None and event.key == pygame.K_RETURN:
                    if 0 <= selected_cat < len(categories):
                        cat = categories[selected_cat]

                        # カスタムダイアログを表示
                        res = edit_category_dialog(cat)

                        # 結果反映
                        if res is not None:
                        # if res["name"]:
                            cat.name = res.get("name", cat.name)
                            cat.alert = res.get("alert", cat.alert)
                            cat.color = res.get("color", cat.color)
                            cat.power_limit = res.get("power_limit", cat.power_limit)
                        else:
                            continue

            elif event.type == pygame.MOUSEBUTTONDOWN:
                window_w, window_h = screen.get_size()
                scale = min(window_w / DRAW_W, window_h / DRAW_H)
                scaled_w = int(DRAW_W * scale)
                scaled_h = int(DRAW_H * scale)
                offset_x = (window_w - scaled_w) // 2
                offset_y = (window_h - scaled_h) // 2                

                # mouse_pos = event.pos
                mx, my = event.pos


                # 黒帯外なら無視
                if offset_x <= mx < offset_x + scaled_w and offset_y <= my < offset_y + scaled_h:
                    sx = (mx - offset_x) / scale
                    sy = (my - offset_y) / scale
                    pos = (sx, sy)
                else:
                    pos = None  # クリック無効領域

                if event.button == 1: # 左クリック
                    if selected_cat is not None and shift:
                        # Shift+クリックで頂点追加
                        new_point = pos
                        # 選択中の頂点の次に挿入
                        if selected_vertex is not None:
                            ci, vi = selected_vertex
                            cat = categories[ci]
                            cat.points.insert(vi + 1, new_point)
                            selected_vertex = (ci, vi + 1)
                        # 選択中の頂点がない → 通常追加
                        else:
                            cat = categories[selected_cat]
                            cat.points.append(new_point)
                            selected_vertex = (selected_cat, len(cat.points) - 1)
                        # clicked = True
                        continue # 追加後は他の処理をスキップ

                if event.button == 1:  # 左クリック
                    (ci, vi) = get_active_point_index(pos, categories)
                    selected_vertex = (ci, vi) if ci is not None and vi is not None else None
                    selected_cat = get_active_polygon_index(pos, categories)

                    internal_pos = screen_to_internal(
                        event.pos,
                        screen.get_size(),
                        (DRAW_W, DRAW_H)
                    )

                    internal_pos = screen_to_internal(
                        event.pos,
                        screen.get_size(),
                        (DRAW_W, DRAW_H)
                    )

                    if selected_vertex is not None:
                        dragging = True
                        selected_cat = ci
                        # if selected_cat is None:

                        vertex_drag_offset = calc_vertex_drag_offset(
                            categories[ci].points[vi],
                            internal_pos
                        )
                        category_drag_offset = None

                    elif selected_cat is not None:
                        dragging = True
                        selected_vertex = None

                        category_drag_offset = calc_category_or_polygon_drag_offset(
                            categories[selected_cat],
                            internal_pos
                        )
                        vertex_drag_offset = None

                    else:
                        dragging = False
                        selected_vertex = None
                        selected_cat = None


            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False

            elif event.type == pygame.MOUSEMOTION:

                # カテゴリドラッグ移動
                if dragging:
                    if selected_vertex is not None:
                        (ci, vi) = selected_vertex
                        dx, dy = drag_vertex(categories[ci], vi, event.pos, screen, DRAW_W, DRAW_H, SCREEN_W, SCREEN_H, offset=vertex_drag_offset)
                        x, y = categories[ci].points[vi]
                        categories[ci].points[vi] = (x + dx , y + dy)
                    elif selected_cat is not None:
                        dx, dy = drag_category_or_polygon(categories[selected_cat], event.pos, screen, DRAW_W, DRAW_H, SCREEN_W, SCREEN_H, offset=category_drag_offset)
                        cat = categories[selected_cat]
                        cat.points = [(x+dx, y+dy) for (x,y) in cat.points]

        # 内部解像度で全て描画したあと
        sw, sh = screen.get_size()
        target_aspect = 16 / 9
        current_aspect = sw / sh

        # 16:9維持（黒帯あり）
        if current_aspect > target_aspect:
            scaled_h = sh
            scaled_w = int(sh * target_aspect)
        else:
            scaled_w = sw
            scaled_h = int(sw / target_aspect)

        scaled = pygame.transform.smoothscale(draw_surface, (scaled_w, scaled_h))
        screen.fill((0, 0, 0))
        offset_x = (sw - scaled_w) // 2
        offset_y = (sh - scaled_h) // 2
        screen.blit(scaled, (offset_x, offset_y))
        pygame.display.flip()


        clock.tick(60)

