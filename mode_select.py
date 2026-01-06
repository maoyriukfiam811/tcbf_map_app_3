import pygame
import tkinter as tk
import os
from tkinter import filedialog, messagebox
from objects import CategoryShape, DataManager, RotatingRect, TextLabel
from utils import select_background_file, save_bg_path, load_bg_path, select_json_file, load_json_path, save_json_path
from config import font_path

# -----------------------------
# モード選択画面
# -----------------------------
def select_mode(screen, font, bg_image_path=None, json_path=None):
    font_text1 = pygame.font.Font(font_path, 20)
    font_text2 = pygame.font.Font(font_path, 15)

    # --- UI定数 ---
    BG_COLOR     = (245, 245, 245)
    BTN_COLOR    = (230, 230, 230)
    BORDER_COLOR = (60, 60, 60)
    TEXT_COLOR   = (20, 20, 20)
    INFO_COLOR   = (80, 80, 80)

    BTN_W, BTN_H = 320, 70
    BTN_GAP = 20

    bg_image_path = load_bg_path()  # 背景画像パス読み込み
    json_path = load_json_path()  # JSONパス読み込み


    while True:
        sw, sh = screen.get_size()

        cx = sw // 2 - BTN_W // 2
        start_y = sh // 2 - (BTN_H * 2 + BTN_GAP * 1.5)

        # --- ボタン定義 ---
        load_button  = pygame.Rect(cx, start_y, BTN_W, BTN_H) #(x, y, w, h)
        clear_button = pygame.Rect(cx+BTN_W + BTN_GAP, start_y, BTN_W/2, BTN_H)
        image_button = pygame.Rect(cx, start_y + (BTN_H + BTN_GAP), BTN_W, BTN_H)
        edit_button  = pygame.Rect(cx, start_y + (BTN_H + BTN_GAP) * 2, BTN_W, BTN_H)
        map_button   = pygame.Rect(cx, start_y + (BTN_H + BTN_GAP) * 3, BTN_W, BTN_H)

        screen.fill(BG_COLOR)

        # --- ボタン描画 ---
        for btn in (map_button, clear_button, edit_button, image_button, load_button):
            pygame.draw.rect(screen, BTN_COLOR, btn)
            pygame.draw.rect(screen, BORDER_COLOR, btn, 2)

        # --- ボタンラベル ---
        def draw_label_1(text, rect):
            t = font_text1.render(text, True, TEXT_COLOR)
            screen.blit(t, t.get_rect(center=rect.center))
        def draw_label_2(text, rect):
            t = font_text2.render(text, True, TEXT_COLOR)
            screen.blit(t, t.get_rect(center=rect.center))

        draw_label_1("1. MAPファイル.JSONを選択", load_button)
        draw_label_2("MAPファイル新規作成", clear_button)
        draw_label_1("2. 背景画像を選択", image_button)
        draw_label_1("3. カテゴリ設定", edit_button)
        draw_label_1("4. 配置編集（マップ）", map_button)

        # --- Path 表示 ---
        info_y = start_y + (BTN_H + BTN_GAP) * 4 + 20

        bg_text = f"背景 Path : {bg_image_path or '(未設定)'}"
        json_text = f"JSON  Path : {json_path or '(未設定)'}"

        screen.blit(font_text2.render(json_text, True, INFO_COLOR), (cx-sw/4, info_y))
        screen.blit(font_text2.render(bg_text, True, INFO_COLOR), (cx-sw/4, info_y + 28))

        pygame.display.flip()

        # --- イベント処理 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if load_button.collidepoint(event.pos):
                    rects, texts, categories, shapes, filename, full_path = DataManager.load_all(filename=None)
                    if full_path:
                        json_path = full_path

                if image_button.collidepoint(event.pos):
                    bg_image_path = select_background_file()
                    if bg_image_path:
                        save_bg_path(bg_image_path)

                if edit_button.collidepoint(event.pos):
                    rects, texts, categories, shapes, filename, full_path = DataManager.load_all(filename=json_path)
                    return "edit", rects, texts, categories, shapes, filename, full_path

                if map_button.collidepoint(event.pos):
                    rects, texts, categories, shapes, filename, full_path = DataManager.load_all(filename=json_path)
                    return "map" , rects, texts, categories, shapes, filename, full_path
                
                if clear_button.collidepoint(event.pos):
                    rects, texts, categories, shapes, filename, full_path = [], [], [], [], None, None
                    json_path = None

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    rects, texts, categories, shapes, filename, full_path = DataManager.load_all(filename=None)
                    if full_path:
                        json_path = full_path
                        save_json_path(json_path)

                if event.key == pygame.K_2:
                    bg_image_path = select_background_file()
                    if bg_image_path:
                        save_bg_path(bg_image_path)

                if event.key == pygame.K_3:
                    rects, texts, categories, shapes, filename, full_path = DataManager.load_all(filename=json_path)
                    return "edit", rects, texts, categories, shapes, filename, full_path

                if event.key == pygame.K_4:
                    rects, texts, categories, shapes, filename, full_path = DataManager.load_all(filename=json_path)
                    return "map", rects, texts, categories, shapes, filename, full_path



# def select_mode(screen, font, bg_image_path=None):

#     while True:
#         sw, sh = screen.get_size()
#         load_data_button   = pygame.Rect(sw/2 - 160, sh/2-120, 320, 80) #(x, y, w, h)
#         map_button   = pygame.Rect(sw/2 - 160, sh/2-120, 320, 80) 
#         edit_button  = pygame.Rect(sw/2 - 160, sh/2,     320, 80)
#         image_button = pygame.Rect(sw/2 - 160, sh/2+120, 320, 80)
    
#         screen.fill((250,250,255))

#         pygame.draw.rect(screen, (100,200,255), map_button)
#         pygame.draw.rect(screen, (120,255,150), edit_button)
#         pygame.draw.rect(screen, (255,220,180), image_button)
#         pygame.draw.rect(screen, (0,0,0), map_button, 3)
#         pygame.draw.rect(screen, (0,0,0), edit_button, 3)
#         pygame.draw.rect(screen, (0,0,0), image_button, 3)

#         # ボタン名表示
#         text = font.render("マップ", True, (0,0,0))
#         rect = text.get_rect(center=map_button.center)
#         screen.blit(text, rect)

#         text = font.render("カテゴリ", True, (0,0,0))
#         rect = text.get_rect(center=edit_button.center)
#         screen.blit(text, rect)

#         text = font.render("背景選択", True, (0,0,0))
#         rect = text.get_rect(center=image_button.center)
#         screen.blit(text, rect)

#         pygame.display.flip()

#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 return None
#             if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
#                 if map_button.collidepoint(event.pos):
#                     return "map"
#                 if edit_button.collidepoint(event.pos):
#                     return "edit"
#                 if image_button.collidepoint(event.pos):
#                     bg_image_path = select_background_file()
#                     if bg_image_path:
#                         save_bg_path(bg_image_path)
#             elif event.type == pygame.KEYDOWN:
#                 if event.key == pygame.K_1:
#                         return "map"
#                 if event.key == pygame.K_2:
#                         return "edit"
#                 if event.key == pygame.K_3:
#                         bg_image_path = select_background_file()
#                         if bg_image_path:
#                             save_bg_path(bg_image_path)