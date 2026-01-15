import os
import pygame
from config import font_path
from mode_select import select_mode
from map_mode import run_map_mode
from objects import RotatingRect, TextLabel, CategoryShape
from utils import select_background_file, save_bg_path
from category_mode import run_category_editor
from objects import DataManager

# -----------------------------
# メイン関数
# -----------------------------
def main():
    # 🟩 ウィンドウ位置を中央に配置
    os.environ['SDL_VIDEO_CENTERED'] = '1'

    pygame.init()
    pygame.font.init()
    pygame.display.set_caption("TCBF_MAP_APP") # ウィンドウタイトル


    SCREEN_W, SCREEN_H = 1280, 720
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)

    try:
        font = pygame.font.Font(font_path, 20)
    except Exception:
        font = pygame.font.SysFont(None, 20)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            return
        # ウィンドウリサイズ処理
        elif event.type == pygame.VIDEORESIZE:
            SCREEN_W, SCREEN_H = event.w, event.h
            screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)

    # categories = CategoryShape.load_categories()  # カテゴリ読み込み

    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                SCREEN_W, SCREEN_H = event.w, event.h
                screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)

        mode, rects, texts, categories, polygons, filename, full_path = select_mode(screen, font)
        if mode is None:
            # モード選択画面で終了
            # CategoryShape.save_categories(categories)
            # rects = RotatingRect.load_rects()
            # texts = TextLabel.load_texts()
            # RotatingRect.save_rects(rects)
            # TextLabel.save_texts(texts)
            print("quit")
            break

        if mode == "map":
            # rects, texts, categories, filename, full_path = DataManager.load_all()
            res = run_map_mode(screen, font, rects, texts, categories, polygons, filename)
            if res is None:
                # running = False
                break
            if res == "back_to_mode_select":
                pygame.display.set_caption("マップ / カテゴリ編集ツール") # ウィンドウタイトル
                continue
        elif mode == "edit":
            # rects, texts, categories, filename, full_path = DataManager.load_all()
            res = run_category_editor(screen, font, rects, texts, categories, polygons, filename)
            if res is None:
                # running = False
                break
        elif mode == "image":
            path = select_background_file()
            if path:
                save_bg_path(path)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
