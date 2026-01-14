import pygame
import tkinter as tk
import config
from config import (
    font_path, SCREEN_W, SCREEN_H, DRAW_W, DRAW_H, MENU_ITEMS_ADD_SHAPE
    )
from objects import (
    PolygonShape, ContextMenu, RotatingRect, TextLabel, DataManager, 
    add_rect, add_polygon
    )
from object_editor import confirm_quit ,edit_object_window, edit_all_objects_window, show_power_table_with_category, edit_polygon_window
from utils import (
    point_in_category, save_as_png, draw_background, load_and_resize_bg, drag_object, rotate_angle, 
    delete_object, undo_delete_object, categories_name_containing_rect, handle_key_movement, move_active_rects, load_bg_path,
    categories_power_list, count_total_by_classification, drag_category_or_polygon, screen_to_internal, convert_mouse_to_draw_coords,
    )

# -----------------------------
# マップ表示モード
# -----------------------------
def run_map_mode(screen, font, rects, texts, categories, polygons, filename):
    """マップ表示用モード"""
    DRAW_W, DRAW_H = 1920, 1080  # 内部描画解像度（固定）
    draw_surface = pygame.Surface((DRAW_W, DRAW_H))  # 内部用Surface
    pygame.display.set_caption(f"{filename}")
    clock = pygame.time.Clock()
    if not rects:
        # 初期サンプル
        rects = [
            RotatingRect(name="testA", center=(320,180), size=(25,25)),
            RotatingRect(name="testB", center=(420,240), size=(25,25), color=(120,180,220)),
        ]
    if not texts:
        texts = [
            TextLabel(text="タイトル（削除不可）", position=(10,20), font_size=20, color=(0,0,0), angle=0, locked=True),
        ]
    if not categories:
        categories = []
    if not polygons:
        polygons = []

    active = None
    active_rects = []
    active_true = False
    name_pos = None
    move_delay = 0.5
    last_move_time = 0
    hide_texts = False # テキスト表示
    hide_until = 0 # テキスト非表示終了時間
    show_category = True
    selected_vertex = None

    need_redraw = False
    ime_warned_message_until = 0 #日本語入力時警告
    export_message_until = 0 # 保存メッセージ表示終了時間
    save_message_until = 0 # 保存メッセージ表示終了時間
    clicked = False # クリックフラグ
    context_menu = None # コンテキストメニュー(右クリック)
    hit_rect = False
    tent_highlight = False
    show_menu = False
    prev_keys = pygame.key.get_pressed()
    font_small = pygame.font.Font(font_path, 15)

    bg_image_path = load_bg_path()
    bg_image = load_and_resize_bg(bg_image_path) if bg_image_path else None

    edit_object_window_results = None


    # shapes cache
    shape_layer = pygame.Surface((DRAW_W, DRAW_H), pygame.SRCALPHA)

    # 背景静的表示
    background_layer = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    def redraw_background_layer():
        background_layer.fill((0,0,0,0))
        if bg_image:
            background_layer.blit(bg_image, (0, 0))
        else:
            background_layer.fill((250,250,255))

    # カテゴリ描画の静的表示
    category_layer = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    def redraw_category_layer():
        """
        map_mode用
        カテゴリ描画を固定キャッシュ化
        """
        category_layer.fill((0,0,0,0))  # 透明クリア
        for cat in categories:
            cat.draw_category(
                category_layer, font,
                active=False, active_vertex=None,
                show_names=False, show_vertices=False
            )

    # レイヤー設定
    redraw_background_layer()
    redraw_category_layer()

    # 背景・カテゴリを画面に1回描画
    screen.blit(background_layer, (0,0))
    screen.blit(category_layer, (0,0))
    pygame.display.flip()

    ACTION_HANDLERS = {
        "add_rect": add_rect,
        "add_polygon": add_polygon,
        # "add_circle": add_circle,
    }


    # ALERT表示
    alert_cats = []
    alert_cats = [c for c in categories if c.alert]
    show_alert = False

    running = True
    while running:
        now = pygame.time.get_ticks() / 1000.0


        # ---- 内部Surfaceにすべて描画 ----
        if need_redraw:
            draw_surface.blit(background_layer, (0,0))

        # # ---- 内部Surfaceにすべて描画 ----
        # if need_redraw:
        #     draw_surface.blit(background_layer, (0,0))

        #     if shape_dirty:
        #         rebuild_shape_layer()
        #         shape_dirty = False
        #     draw_surface.blit(shape_layer, (0,0))

        #     if show_category:
        #         draw_surface.blit(category_layer, (0,0))

        #     pygame.display.flip()
        #     need_redraw = False

        # カテゴリ描画（名前非表示）
        draw_surface.blit(background_layer, (0,0))
        draw_surface.blit(shape_layer, (0,0))

        if show_category:
            draw_surface.blit(category_layer, (0,0))

        # 四角形描画
        dirty = []
        
        # すべての rect の dirty を消す
        for obj in rects:
            for r in obj.prev_dirty:
                draw_surface.blit(background_layer, r, r)
                draw_surface.blit(shape_layer, r, r)
                if show_category:
                    draw_surface.blit(category_layer, (0,0))
                dirty.append(r)

        # rect を新しく描画
        for obj in rects:
            is_active = (obj == active) or (obj in active_rects)
            new_dirty = obj.draw_rects(draw_surface, font, is_active=is_active, name_pos_active=obj.name_pos_active, tent_highlight=tent_highlight)
            dirty.extend(new_dirty)
            obj.prev_dirty = new_dirty

        
        # Polygon 描画
        for poly in polygons:
            is_active = (poly == active)
            new_dirty = poly.draw_polygon(
                draw_surface,
                is_active=is_active
            )
            dirty.extend(new_dirty)
            poly.prev_dirty = new_dirty


        # 画面に反映
        pygame.display.update(dirty)

        ### 確認用 ###
        # draw_surface.blit(font_small.render(f"len(active_rects):, {len(active_rects)}", True, (0,0,0)), (10, 300))
        # draw_surface.blit(font_small.render(f"active:, {active}", True, (0,0,0)), (10, 320))

        # テキスト描画
        for t in texts:
            t.draw_texts(draw_surface, font_path, active=(t is active))

        # --- 保存メッセージ表示 ---
        if now < save_message_until:
            msg_surf = font.render("Saved all objects.", True, (0, 0, 0))
            draw_surface.blit(msg_surf, (DRAW_W - msg_surf.get_width() - 10, 10))
        if now < export_message_until:
            msg_surf = font.render("CSV has been exported.", True, (0, 0, 0))
            draw_surface.blit(msg_surf, (DRAW_W - msg_surf.get_width() - 10, 10))

        # イベント処理
        keys = pygame.key.get_pressed()
        if active:
            if isinstance(active, RotatingRect):
                if active and active.name_pos_active:
                    x, y = active.name_pos
                    x, y, last_move_time = handle_key_movement(
                        now, last_move_time, move_delay, keys, prev_keys, ctrl, shift, x, y, w=SCREEN_W, h=SCREEN_H
                    , allow_negative=True)
                    active.name_pos = (x,y)
                elif not active.name_pos_active:
                    x, y = active.center
                    x, y, last_move_time = handle_key_movement(
                        now, last_move_time, move_delay, keys, prev_keys, ctrl, shift, x, y, w=SCREEN_W, h=SCREEN_H
                    )
                    active.center = (x, y)

            elif isinstance(active, TextLabel):
                x, y = active.position
                x, y, last_move_time = handle_key_movement(
                    now, last_move_time, move_delay, keys, prev_keys, ctrl, shift, x, y, w=SCREEN_W, h=SCREEN_H
                )
                active.position = (x, y)

            elif isinstance(active, PolygonShape):
                if selected_vertex is not None:
                    pi, vi = selected_vertex
                    x, y = polygons[int(pi)].points[int(vi)]
                    dx, dy, new_x, new_y, last_move_time = handle_vertex_movement(
                        x, y, now, last_move_time, move_delay,
                        keys, prev_keys, ctrl, shift, step=5, w=SCREEN_W, h=SCREEN_H)
                    polygons[int(pi)].points[vi] = (new_x, new_y)

                else:
                    pi = polygons.index(active)
                    last_move_time = handle_category_movement(
                        polygons[pi], now, last_move_time, move_delay,
                        keys, prev_keys, ctrl, shift)                

        elif active_rects:
            last_move_time = move_active_rects(active, active_rects,now, last_move_time, move_delay, keys, prev_keys, ctrl, shift, SCREEN_W, SCREEN_H)

        prev_keys = keys

        # category表示制御
        if not show_category and now > hide_until:
            show_category = True
            need_redraw = True

        #操作説明表示制御
        hide_texts = now < hide_until
        hide = True
        if hide_texts:
            None
        elif not hide_texts:
        # elif not hide:

            # --- 操作説明表示 ---
            if active is None:
                instructions = [
                    "クリック: オブジェクト選択",
                    "Ctrl+クリック: オブジェクト複数選択",
                    "ドラッグ: オブジェクト移動",
                    "N: 四角新規追加",
                    "T: テキスト新規追加",
                    "O: 全オブジェクト編集",
                    "P: 全電力編集",
                    "H: テント貸出ハイライト表示",
                    "Ctrl+S: 保存",
                    "ESC: 保存して戻る",
                    "Ctrl+Z: 元に戻す（削除のみ）",
                    "Ctrl+P: pngとして保存",
                    "Ctrl+E: csvとしてエクスポート",
                    "Ctrl+H: 操作説明非表示5秒間",
                ]

            elif isinstance(active, RotatingRect):
                instructions = [
                    "ドラッグ, 矢印キー: 移動",
                    "空白クリック: 選択解除",
                    "Shift+矢印キー: 10px移動",
                    "Ctrl+矢印キー: 50px移動",
                    "1 / 3: 回転",
                    "Tab: 切替/選択"
                    "Enter: 編集",
                    "Delete: 削除",
                    "Ctrl+Z: 元に戻す（削除のみ）",
                    "A / D: 高さ幅変更",
                    "W / S: 高さ変更",
                    "Q / E: 幅変更",
                    ";(+) / -: 名前サイズ変更",
                    "Space: 名前位置編集切替",
                    # "N: 四角新規追加",
                    # "T: テキスト新規追加",
                    # "O: 全オブジェクト編集",
                    # "Ctrl+S: 保存",
                    # "ESC: 保存して戻る",
                    # "Ctrl+P: pngとして保存",
                    # "Ctrl+H: 操作説明非表示5秒間",
                ]

            elif isinstance(active, TextLabel):
                instructions = [
                    "ドラッグ, 矢印キー: 移動",
                    "Shift+矢印キー: 10px移動",
                    "Ctrl+矢印キー: 50px移動",
                    "1 / 3: 回転",
                    "T: テキスト編集",
                    "Delete: 削除",
                    "Ctrl+Z: 元に戻す（削除のみ）",
                    "N: 四角新規追加",
                    "T: テキスト新規追加",
                    "O: 全オブジェクト編集",
                    # "Ctrl+S: 保存",
                    # "ESC: 保存して戻る",
                    # "Ctrl+P: pngとして保存",
                    # "Ctrl+H: 操作説明非表示5秒間",
                ]


            # ALERT描画
            alert_cats_name = []
            for rect in rects:
                for cat in alert_cats:
                    if point_in_category(rect.center, cat):
                        alert_cats_name.append(cat.name)
            if alert_cats_name:
                show_alert = True
                show_alert_text = ", ".join(alert_cats_name)
            else:
                show_alert = False

            if show_alert:
                alert_text = pygame.font.Font(font_path, 30).render(f"注意: {show_alert_text}", True, (255, 0, 0))
                w, h = draw_surface.get_size()
                draw_surface.blit(alert_text, (w - alert_text.get_width() - 10, h - alert_text.get_height() - 10))


            # --- 描画（左下配置） ---
            y_offset = DRAW_H - 20 * len(instructions) - 10  # 下端から上にずらす
            x_offset = 10  # 左端から10px
            for i, line in enumerate(instructions):
                text_surf = font_small.render(line, True, (0, 0, 0))
                draw_surface.blit(text_surf, (x_offset, y_offset + i * 20))

            # --- アクティブオブジェクト情報表示 ---
            if isinstance(active, RotatingRect): #単一選択
                draw_surface.blit(font_small.render(f"no: {active.no}", True, (0,0,0)), (10, 50)) #1行目
                info_name = active.name.replace("\\n","").replace("\n","")
                draw_surface.blit(font_small.render(f"name: {info_name}", True, (0,0,0)), (10, 70)) #2行目以降
                draw_surface.blit(font_small.render(f"area:", True, (0,0,0)), (10, 90))
                draw_surface.blit(font_small.render(f"classification: {active.classification if active else ''}", True, (0,0,0)), (10, 110))
                draw_surface.blit(font_small.render(f"power [W]: {active.power if active else ''}", True, (0,0,0)), (10, 130))
                draw_surface.blit(font_small.render(f"rect_size: {active.size if active else ''}", True, (0,0,0)), (10, 150))
                draw_surface.blit(font_small.render(f"angle: {active.angle if active else ''}", True, (0,0,0)), (10, 170))
                draw_surface.blit(font_small.render(f"font_size: {active.font_size if active else ''}", True, (0,0,0)), (10, 190))
                draw_surface.blit(font_small.render(f"name_angle: {active.name_angle if active else ''}", True, (0,0,0)), (10, 210))
                draw_surface.blit(font_small.render(f"rect_position: {active.center if active else ''}", True, (0,0,0)), (10, 230))
                name_pos_0 = active.name_pos[0] + active.center[0]
                name_pos_1 = active.name_pos[1] + active.center[1]
                name_pos = (name_pos_0, name_pos_1)
                draw_surface.blit(font_small.render(f"name_position: {name_pos if active else ''}", True, (0,0,0)), (10, 250))

                if active:
                    categories_name_list = categories_name_containing_rect(active.center, categories)
                    if categories_name_list:
                        category_names = ", ".join(map(str, sorted(set(categories_name_list))))
                    else:
                        category_names = "None"
                    text_surface = font_small.render(category_names, True, (0, 0, 0))
                    draw_surface.blit(text_surface, (55, 90))

            elif active_rects: #複数選択
                active_rects = sorted(active_rects, key=lambda r: r.no)
                cleaned_names = [r.name.replace("\\n", "").replace("\n", "") for r in active_rects]
                ids = ", ".join(str(r.no) for r in active_rects)
                names = ", ".join(cleaned_names)
                classes = ", ".join(sorted({r.classification for r in active_rects}))
                powers = ", ".join(sorted(str(r.power) for r in active_rects))
                rect_sizes = ", ".join(sorted(f"{size}"for size in {r.size for r in active_rects}))
                font_sizes = ", ".join(sorted({str(r.font_size) for r in active_rects}))

                draw_surface.blit(font_small.render(f"no: {ids}", True, (0,0,0)), (10, 50)) #1行目
                draw_surface.blit(font_small.render(f"name: {names}", True, (0,0,0)), (10, 70)) #2行目以降
                draw_surface.blit(font_small.render(f"area: ", True, (0,0,0)), (10, 90))
                draw_surface.blit(font_small.render(f"classification: {classes}", True, (0,0,0)), (10, 110))
                draw_surface.blit(font_small.render(f"power [W]: {powers}", True, (0,0,0)), (10, 130))
                draw_surface.blit(font_small.render(f"rect_size: {rect_sizes}", True, (0,0,0)), (10, 150))
                draw_surface.blit(font_small.render(f"angle: ", True, (0,0,0)), (10, 170))
                draw_surface.blit(font_small.render(f"font_size: {font_sizes}", True, (0,0,0)), (10, 190))
                draw_surface.blit(font_small.render(f"name_angle: ", True, (0,0,0)), (10, 210))
                draw_surface.blit(font_small.render(f"center: ", True, (0,0,0)), (10, 230))

                if active_rects:
                    # --- すべての rect のカテゴリ名を取得 ---
                    all_category_names = [
                        name
                        for r in active_rects
                        for name in (categories_name_containing_rect(r.center, categories) or [])
                    ]

                    category_names = (
                        ", ".join(sorted(set(all_category_names)))
                        if all_category_names else "None"
                    )
                    text_surface = font_small.render(category_names, True, (0, 0, 0))
                    draw_surface.blit(text_surface, (55, 90))


            # 各クラス毎の総数表示（右上）
            total_counts = count_total_by_classification(rects)
            base_x = DRAW_W - 10
            base_y = 50
            line_h = 20

            y = base_y

            for key in sorted(total_counts.keys()):
                text = f"{key}: {total_counts[key]}"
                text_surf = font_small.render(text, True, (0, 0, 0))

                x = base_x - text_surf.get_width()  # 右揃え
                draw_surface.blit(text_surf, (x, y))

                y += line_h


            # --- 電力合計表示 ---
            power_totals, sorted_categories = categories_power_list(rects, categories, point_in_category)

            base_y, line_h = 290, 20

            power_limit_map = {c.name: c.power_limit for c in sorted_categories}

            for i, (name, power) in enumerate(sorted(power_totals.items())):
                power_limit = int(power_limit_map.get(name, 0))

                y = base_y + i * line_h

                # --- 超過判定 ---
                if power_limit > 0 and power > power_limit:
                    color = (255, 0, 0)   # 赤
                else:
                    color = (0, 0, 0)     # 黒

                text = f"{name}: {power}[W]/{power_limit}[W]"
                surf = font_small.render(text, True, color)
                draw_surface.blit(surf, (10, y))


        #ウィンドウに描画
        keys = pygame.key.get_pressed()
        mods = pygame.key.get_mods()
        ctrl = mods & pygame.KMOD_CTRL
        shift = mods & pygame.KMOD_SHIFT

        pygame.key.start_text_input()

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                res = confirm_quit()
                if res:
                    DataManager.save_all(rects, texts, categories, polygons, filename)
                    return "back_to_mode_select"
                elif res is False:
                    running = False
                elif res is None:
                    pass

            # --- RotatingRect AND TextLabel IS NOT ACTIVE ---
            # ウィンドウリサイズ処理
            elif event.type == pygame.VIDEORESIZE:
                bg_image = load_and_resize_bg(bg_image_path) if bg_image_path else None
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

            # # IME ON(日本語入力)
            # elif event.type == pygame.TEXTINPUT:
            #     print("IME ON -> IME OFF.")
            #     ime_warned_message_until = now + 3  # 今から3秒後
            #     continue

            elif event.type == pygame.KEYDOWN:
                # ACTIVE OBJECT MOVEMENT
                if isinstance(active, RotatingRect) and event.key == pygame.K_SPACE:    
                    active.name_pos_active = not active.name_pos_active # 名前位置編集モード切替
                if event.key == pygame.K_ESCAPE:
                    # 1. 複数選択中なら解除
                    if len(active_rects) > 0:
                        for r in active_rects:
                            r.name_pos_active = False
                        active_rects = []
                        active = None
                        continue
                    # 2. 単一の四角が active なら name_pos_active 解除して終了
                    if isinstance(active, RotatingRect):
                        if active.name_pos_active:
                            active.name_pos_active = False
                            active = None
                            continue
                        else:
                            active = None
                            continue
                    # 3. テキストが active なら単に解除
                    if isinstance(active, TextLabel):
                        active = None
                        continue
                    # 4. 何も選択していない → 初めてモードセレクトへ戻る
                    if active is None and len(active_rects)==0:
                        res = confirm_quit()
                        if res:
                            DataManager.save_all(rects, texts, categories, polygons, filename)
                            return "back_to_mode_select"
                        elif res is False:
                            return "back_to_mode_select"
                        elif res is None:
                            pass

                # SAVE
                if ctrl and event.key == pygame.K_s:
                    DataManager.save_all(rects, texts, categories, polygons, filename)
                    print("Saved all objects.")
                    save_message_until = now + 3  # 今から3秒後
                # ADD NEW RECT
                if isinstance(active, RotatingRect) or active is None:
                    if event.key == pygame.K_n:
                        if not active:
                            new = RotatingRect(name=f"Rect{len(rects)+1}", center=(SCREEN_W//2, SCREEN_H//2), size=(25,25))
                            # name_pos_active = False
                        elif active:
                            x,y = active.center
                            new = RotatingRect(
                                name=f"Rect{len(rects)+1}", 
                                center=(x+20, y+20), 
                                size=active.size, 
                                name_pos=active.name_pos, 
                                name_angle=active.name_angle, 
                                classification=active.classification,
                                color=active.color,
                                font_size=active.font_size,
                                )
                        rects.append(new)
                        active = new
                        active.name_pos_active = False
                # ADD NEW TEXT LABEL
                if isinstance(active, TextLabel) or active is None:    
                    if event.key == pygame.K_t:
                        if not active:
                            new = TextLabel(text=f"Label{len(texts)+1}", position=(SCREEN_W//2, SCREEN_H//2), font_size=20, color=(0,0,0))
                        elif active:
                            x,y = active.position
                            new = TextLabel(text=f"Label{len(texts)+1}", position=(x+20, y+20), font_size=20, color=(0,0,0))
                        texts.append(new)
                        active = new

                # EDIT_ALL_OBJECTS_WINDOW
                if event.key == pygame.K_o:
                    objs =  edit_all_objects_window(rects)
                    rects = objs

                # EDIT_OBJECT_WINDOW
                if isinstance(active, RotatingRect):    
                    if active and event.key == pygame.K_RETURN:
                        edit_object_window_results = edit_object_window(active)

                        for i in range(len(edit_object_window_results)):
                            active.no = edit_object_window_results["no"]
                            active.name = edit_object_window_results["name"]
                            active.text = edit_object_window_results["text"]
                            active.center = edit_object_window_results["center"]
                            active.position = edit_object_window_results["position"]
                            active.color = edit_object_window_results["color"]
                            active.classification = edit_object_window_results["classification"]
                            active.power = edit_object_window_results["power"]
                            active.tent = edit_object_window_results["tent"]
                            active.light = edit_object_window_results["light"]

                if event.key == pygame.K_h:
                    # HIDE INFO TEXT for 5 seconds
                    if ctrl:
                        hide_until = now + 5
                        need_redraw = True
                        show_category = False

                    # TENT HIGHLIGHT
                    else:
                        tent_highlight = not tent_highlight

                # SAVE AS PNG
                if ctrl:
                    if event.key == pygame.K_p:
                        save_as_png(draw_surface)
                else:
                    # SHOW_POWER_TABLE_WITH_CATEGORY
                    if event.key == pygame.K_p:
                        show_power_table_with_category(rects, categories, point_in_category)

                # EXPORT AS CSV
                if ctrl and event.key == pygame.K_e:
                    RotatingRect.save_rects_as_csv(rects, categories, point_in_category)
                    print("CSV has been exported.")
                    export_message_until = now + 3  # 今から3秒後

                # UNDO (ONLY DELETE)
                if ctrl and event.key == pygame.K_z:
                    if isinstance(config.last_deleted_obj, RotatingRect):
                        active = undo_delete_object(rects)
                    if isinstance(config.last_deleted_obj, TextLabel):
                        active = undo_delete_object(texts)

                # --- ACTIVE_RECTS IS ACTIVE ---
                if active_rects:
                    # 大きさ変更
                    if event.key == pygame.K_a:
                        for active in active_rects:
                            w,h = active.size
                            w -= 1
                            h -= 1
                            active.size = (w,h)
                    if event.key == pygame.K_d:
                        for active in active_rects:                       
                            w,h = active.size
                            w += 1
                            h += 1
                            active.size = (w,h)
                    # 幅変更
                    if event.key == pygame.K_q:
                        for active in active_rects:
                            w,h = active.size
                            w -= 1
                            active.size = (w,h)
                    if event.key == pygame.K_e:
                        for active in active_rects:
                            w,h = active.size
                            w += 1
                            active.size = (w,h)
                    # 高さ変更
                    if event.key == pygame.K_z:
                        for active in active_rects:
                            w,h = active.size
                            h -= 1
                            active.size = (w,h)
                    if event.key == pygame.K_c:
                        for active in active_rects:
                            w,h = active.size
                            h += 1
                            active.size = (w,h)
                    # 文字高さ変更
                    if event.key == pygame.K_SEMICOLON:
                        for active in active_rects:
                            ns = active.font_size
                            ns += 1
                            active.font_size = ns
                    if event.key == pygame.K_MINUS:
                        for active in active_rects:
                            ns = active.font_size
                            ns = max(1, ns - 1)
                            active.font_size = ns


                # --- RotatingRect IS ACTIVE ---
                if isinstance(active, RotatingRect):
                    if event.key == pygame.K_TAB:
                        # rects を y → x の順でソート（左上から左下方向）
                        sorted_rects = sorted(rects, key=lambda r: (r.center[0], r.center[1]))
                        # 現在の active のインデックスを特定
                        if active in sorted_rects:
                            idx = sorted_rects.index(active)
                            active.name_pos_active = False
                        else:
                            idx = 0  # 念のため
                        # Shift が押されているかで前後切り替え
                        if shift:
                            idx = (idx - 1) % len(sorted_rects)
                        else:
                            idx = (idx + 1) % len(sorted_rects)
                        # 新しいアクティブをセット
                        active = sorted_rects[idx]

                    # 回転操作
                    if active:
                        if not active.name_pos_active:
                            if event.key == pygame.K_1:
                                rotate_angle(active, -5)
                            if event.key == pygame.K_3:
                                rotate_angle(active, +5)
                        elif active and active.name_pos_active:
                            if event.key == pygame.K_1:
                                active.name_angle += 5
                            if event.key == pygame.K_3:
                                active.name_angle -= 5

                    # 大きさ変更
                    if event.key == pygame.K_a:
                        w,h = active.size
                        w -= 1
                        h -= 1
                        active.size = (w,h)
                    if event.key == pygame.K_d:
                        w,h = active.size
                        w += 1
                        h += 1
                        active.size = (w,h)
                    # 幅変更
                    if event.key == pygame.K_q:
                        w,h = active.size
                        w -= 1
                        active.size = (w,h)
                    if event.key == pygame.K_e:
                        w,h = active.size
                        w += 1
                        active.size = (w,h)
                    # 高さ変更
                    if event.key == pygame.K_z:
                        w,h = active.size
                        h -= 1
                        active.size = (w,h)
                    if event.key == pygame.K_c:
                        w,h = active.size
                        h += 1
                        active.size = (w,h)
                    # 文字高さ変更
                    if event.key == pygame.K_SEMICOLON:
                        ns = active.font_size
                        ns += 1
                        active.font_size = ns
                    if event.key == pygame.K_MINUS:
                        ns = active.font_size
                        ns = max(1, ns - 1)
                        active.font_size = ns
                    # DELETE
                    if event.key == pygame.K_DELETE:
                        delete_object(active, rects)
                        active = None
                if not active and not active_rects:
                    if event.key == pygame.K_TAB:
                        active = rects[0]


                # --- TextLabel IS ACTIVE ---
                if isinstance(active, TextLabel):
                    if event.key == pygame.K_TAB:
                        # rects を y → x の順でソート（左上から左下方向）
                        texts = sorted(texts, key=lambda r: (r.position[0], r.position[1]))
                        # 現在の active のインデックスを特定
                        if active in texts:
                            idx = texts.index(active)
                            active.name_pos_active = False
                        else:
                            idx = 0  # 念のため
                        # Shift が押されているかで前後切り替え
                        if shift:
                            idx = (idx - 1) % len(texts)
                        else:
                            idx = (idx + 1) % len(texts)
                        
                        # 新しいアクティブをセット
                        active = texts[idx]

                    # font_size変更
                    if event.key == pygame.K_SEMICOLON:
                        ns = active.font_size
                        ns += 1
                        active.font_size = ns
                    if event.key == pygame.K_MINUS:
                        ns = active.font_size
                        ns = max(1, ns - 1)
                        active.font_size = ns
                    # 回転操作
                    if event.key == pygame.K_1:
                        rotate_angle(active, -5)
                    if event.key == pygame.K_3:
                        rotate_angle(active, 5)
                    # DELETE
                    if event.key == pygame.K_DELETE:
                        if active.locked:
                            pass  # ロックされているので削除不可
                        else:
                            delete_object(active, texts)
                            active = None

                # --- PolygonShape IS ACTIVE ---
                if isinstance(active, PolygonShape):

                    # 削除
                    if event.key == pygame.K_DELETE:
                        delete_object(active, polygons)
                        active = None
                        selected_vertex = None

                    # 頂点選択トグル（SPACE）
                    elif event.key == pygame.K_SPACE:
                        if selected_vertex is None:
                            pi = polygons.index(active)
                            selected_vertex = (pi, 0)  # 最初の頂点を選択
                        else:
                            selected_vertex = None
                        
                    elif event.key == pygame.K_TAB:
                        pi = polygons.index(active)

                        # 頂点選択がある → 頂点移動（従来どおり）
                        if selected_vertex is not None:
                            poly = polygons[pi]
                            _, vi = selected_vertex

                            if shift:
                                vi = (vi - 1) % len(poly.points)
                            else:
                                vi = (vi + 1) % len(poly.points)

                            selected_vertex = (pi, vi)

                        # 頂点未選択 → ポリゴン切り替え
                        else:
                            if shift:
                                pi = (pi - 1) % len(polygons)
                            else:
                                pi = (pi + 1) % len(polygons)

                            active = polygons[pi]
                            selected_vertex = None
                        
                    
                    # 頂点削除（Dキー）
                    elif event.key == pygame.K_d:
                        if selected_vertex is not None:
                            pi, vi = selected_vertex
                            poly = polygons[pi]

                            # 最低2頂点は維持
                            if len(poly.points) > 2:
                                poly.points.pop(vi)

                                # 削除後の選択頂点調整
                                if vi >= len(poly.points):
                                    vi = len(poly.points) - 1

                                selected_vertex = (pi, vi)
                            else:
                                # 削除不可（必要ならログ）
                                print("Polygon must have at least 2 vertices.")
                                pass

                    # 頂点追加（Nキー）
                    elif event.key == pygame.K_n:
                        pi = polygons.index(active)
                        poly = polygons[pi]

                        # 基準頂点を決定
                        if selected_vertex is not None:
                            _, vi = selected_vertex
                        else:
                            vi = 0  # points[0]

                        x, y = poly.points[vi]
                        new_point = (x + 30, y)

                        # 右隣に挿入
                        poly.points.insert(vi + 1, new_point)

                        # 追加した点を選択状態に
                        selected_vertex = (pi, vi + 1)

                    # 編集ウィンドウ表示（ENTERキー）
                    elif event.key == pygame.K_RETURN:
                        edit_polygon_window(active)

                    # アクティブ解除（ESCキー）
                    elif event.key == pygame.K_ESCAPE:
                        if selected_vertex is not None:
                            # 頂点選択解除
                            selected_vertex = None
                        else:
                            # ポリゴン選択解除
                            active = None

            # マウスクリック処理
            elif event.type == pygame.MOUSEBUTTONDOWN:
                sw, sh = screen.get_size()
                scale = min(sw / DRAW_W, sh / DRAW_H)
                scaled_w = int(DRAW_W * scale)
                scaled_h = int(DRAW_H * scale)
                offset_x = (sw - scaled_w) // 2
                offset_y = (sh - scaled_h) // 2

                mx, my = event.pos
                # 黒帯外なら無視
                if offset_x <= mx < offset_x + scaled_w and offset_y <= my < offset_y + scaled_h:
                    sx = (mx - offset_x) / scale
                    sy = (my - offset_y) / scale
                    pos = (sx, sy)
                else:
                    pos = None  # クリック無効領域


                # 右クリックでメニュー生成
                if event.button == 3:
                    temporary_pos = event.pos
                    context_menu = ContextMenu(MENU_ITEMS_ADD_SHAPE, event.pos) # ここで右クリックによる形状追加itemsを渡す
                    continue

                # メニューがある場合は最優先で処理
                if context_menu:
                    action = context_menu.handle_event(event) #返値は追加アクション名 / 例："add_rect"
                    if action:
                        if action == "add_rect":
                            new = add_rect(rects, active, temporary_pos, screen, context_menu=True)
                            rects.append(new)
                            active = new
                    if action:
                        if action == "add_polygon":
                            new = add_polygon(polygons, active, temporary_pos, screen, context_menu=True)
                            polygons.append(new)
                            active = new
                    if not context_menu.visible:
                        context_menu = None
                    continue

                    
                # 四角形選択・ドラッグ開始
                for r in reversed(rects): # 手前の四角形から優先的に選択
                    # 複数アクティブ
                    if ctrl:
                        if r.contains_point(pos):
                            clicked_rect = r
                            if clicked_rect in active_rects:
                                active_rects.remove(clicked_rect)
                            elif clicked_rect not in active_rects:
                                if active == clicked_rect:
                                    active_rects.append(clicked_rect)
                                    active = None
                                    for r in rects:
                                        r.name_pos_active = False
                                elif active:
                                    active_rects.append(active)
                                    active_rects.append(clicked_rect)
                                    active = None
                                    for r in rects:
                                        r.name_pos_active = False
                                elif active is None:
                                    active_rects.append(clicked_rect)
                        # else:
                        #     None
                 # 通常アクティブ
                    else:
                        if r.contains_point(pos):
                            active = r
                            r.dragging = True
                            r.drag_offset = (r.center[0]-pos[0], r.center[1]-pos[1])
                            clicked = True
                            break
                        else:
                            r.name_pos_active = False
                            active = None
                            # テキスト選択・ドラッグ開始
                            for t in reversed(texts): # 手前のテキストから優先的に選択
                                if t.contains_point(pos, font_path):
                                    active = t
                                    t.dragging = True
                                    t.drag_offset = (t.position[0]-pos[0], t.position[1]-pos[1])  
                                    clicked = True
                                    break
                                else:
                                    active = None
                                    active_rects = []

                for p in reversed(polygons):
                    if p.contains_line(pos):
                        active = p
                        clicked = True
                        p.dragging = True

                        internal_pos = screen_to_internal(
                            event.pos,
                            screen.get_size(),
                            (DRAW_W, DRAW_H)
                        )

                        category_drag_offset = (
                            active.points[0][0] - internal_pos[0],
                            active.points[0][1] - internal_pos[1]
                        )
                        break
                    else:
                        active = None
                        active_rects = []


            elif event.type == pygame.MOUSEBUTTONUP:
                if isinstance(active, RotatingRect):    
                    for r in rects:
                        r.dragging = False
                elif isinstance(active, TextLabel):
                    for t in texts:
                        t.dragging = False
                elif isinstance(active, PolygonShape):
                    for p in polygons:
                        p.dragging = False


            elif event.type == pygame.MOUSEMOTION:
                if active is not None:
                    drag_object(
                        active,
                        event.pos,
                        screen,
                        SCREEN_W,
                        SCREEN_H
                    )


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

        # コンテキストメニュー描画
        if context_menu:
            context_menu.draw(screen, font_small)


        pygame.display.flip()

        clock.tick(60) # FPS
