import pygame
import sys
import csv
import os
import math
from typing import List, Tuple, Optional

# ==========================================
# 설정 및 상수 (config.py, asset_paths.py 연동)
# ==========================================
try:
    from config import (
        SCREEN_WIDTH, SCREEN_HEIGHT, CELL_SIZE, BUBBLE_RADIUS,
        MAP_ROWS, MAP_COLS, FPS, SCALE  # SCALE 추가 임포트
    )
    from asset_paths import ASSET_PATHS
    from color_settings import COLORS
except ImportError:
    print("설정 파일을 찾을 수 없습니다. config.py 등이 같은 폴더에 있는지 확인해주세요.")
    sys.exit()

# ==========================================
# UI 디자인 상수
# ==========================================
THEME_BG = (10, 20, 40)
THEME_PANEL = (20, 30, 60)
THEME_BORDER = (145, 233, 239)
TEXT_COLOR = (255, 255, 255) # 텍스트는 흰색이 가독성이 좋아 수정 (원하시는대로 변경 가능)
BTN_HOVER = (50, 100, 150)
BTN_IDLE = (168, 212, 246)

# ==========================================
# 유틸리티 & UI 클래스
# ==========================================
def clamp(v, lo, hi):
    return max(lo, min(hi, v))

class Button:
    def __init__(self, x, y, w, h, text, callback, color=BTN_IDLE, image=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.base_color = color
        self.hover_color = BTN_HOVER
        self.is_hovered = False
        self.image = image

    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.base_color
        # 테두리 반경도 스케일에 맞춰 조정
        radius = int(10 * SCALE)
        pygame.draw.rect(screen, color, self.rect, border_radius=radius)
        pygame.draw.rect(screen, THEME_BORDER, self.rect, max(1, int(2 * SCALE)), border_radius=radius)
        
        if self.image:
            img_rect = self.image.get_rect(center=self.rect.center)
            screen.blit(self.image, img_rect)
        
        if self.text:
            # 텍스트 색상을 TEXT_COLOR 상수가 아닌 검정(버튼 위 가독성)으로 하거나 선택
            txt = font.render(self.text, True, (0,0,0)) 
            t_rect = txt.get_rect(center=self.rect.center)
            screen.blit(txt, t_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                if self.callback:
                    self.callback()

# ==========================================
# 장식용 캐논 클래스
# ==========================================
class DecorCannon:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 90
        try:
            self.arrow_image = pygame.image.load(ASSET_PATHS['cannon_arrow']).convert_alpha()
            # 이미지 크기도 스케일에 맞춰 조정
            w = int(152 * SCALE)
            h = int(317 * SCALE)
            self.arrow_image = pygame.transform.smoothscale(self.arrow_image, (w, h))
        except:
            self.arrow_image = None

    def draw(self, screen):
        if self.arrow_image:
            rotated = pygame.transform.rotate(self.arrow_image, self.angle - 90)
            rect = rotated.get_rect(center=(self.x, self.y))
            screen.blit(rotated, rect)
        else:
            line_len = int(100 * SCALE)
            width = max(1, int(4 * SCALE))
            pygame.draw.line(screen, (255,255,255), (self.x, self.y), (self.x, self.y-line_len), width)

# ==========================================
# 에디터용 그리드
# ==========================================
class EditorGrid:
    def __init__(self, x_offset, y_offset, bubble_images):
        self.rows = MAP_ROWS
        self.cols = MAP_COLS
        self.cell = CELL_SIZE # config에서 이미 스케일링 된 값
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.bubble_images = bubble_images
        self.map = [['.' for _ in range(self.cols)] for _ in range(self.rows)]

    def get_cell_center(self, r, c):
        x = c * self.cell + self.cell // 2 + self.x_offset
        y = r * self.cell + self.cell // 2 + self.y_offset
        if r % 2 == 1:
            x += self.cell // 2
        return x, y

    def screen_to_grid(self, x, y):
        r = int((y - self.y_offset) // self.cell)
        c_base = x - self.x_offset
        if r % 2 == 1:
            c = int((c_base - self.cell // 2) // self.cell)
        else:
            c = int(c_base // self.cell)
        return r, c

    def is_in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def set_cell(self, r, c, color_code):
        if self.is_in_bounds(r, c):
            self.map[r][c] = color_code

    def draw(self, screen):
        for r in range(self.rows):
            for c in range(self.cols):
                if r % 2 == 1 and c == self.cols - 1:
                    continue

                cx, cy = self.get_cell_center(r, c)
                color_code = self.map[r][c]

                if color_code in self.bubble_images:
                    img = self.bubble_images[color_code]
                    rect = img.get_rect(center=(cx, cy))
                    screen.blit(img, rect)
                elif color_code == '.' or color_code == 'X':
                    # BUBBLE_RADIUS는 config에서 이미 스케일링 됨
                    pygame.draw.circle(screen, (30, 50, 80), (cx, cy), BUBBLE_RADIUS, 1)

# ==========================================
# 메인 에디터 클래스
# ==========================================
class MapEditor:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Bubble Pop - Map Editor")
        self.clock = pygame.time.Clock()
        
        # --- 폰트 (크기 스케일링 적용) ---
        self.font_path = ASSET_PATHS.get('font')
        if self.font_path and os.path.exists(self.font_path):
            self.font_ui = pygame.font.Font(self.font_path, int(30 * SCALE))
            self.font_title = pygame.font.Font(self.font_path, int(50 * SCALE))
            self.font_big = pygame.font.Font(self.font_path, int(80 * SCALE))
        else:
            self.font_ui = pygame.font.Font(None, int(30 * SCALE))
            self.font_title = pygame.font.Font(None, int(50 * SCALE))
            self.font_big = pygame.font.Font(None, int(80 * SCALE))

        # --- 이미지 에셋 로드 ---
        self.bubble_images = {}
        # BUBBLE_RADIUS는 config에서 이미 스케일링 되어있으므로 그대로 사용
        target_size = BUBBLE_RADIUS * 2
        color_key_map = {
            'R': 'bubble_red', 
            'Y': 'bubble_yellow', 
            'B': 'bubble_blue', 
            'G': 'bubble_green',
            'N': 'bubble_obstacle'  # 장애물 버블 추가
        }
        
        for code, asset_key in color_key_map.items():
            path = ASSET_PATHS.get(asset_key)
            if path and os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.smoothscale(img, (target_size, target_size))
                self.bubble_images[code] = img
            else:
                # 장애물은 회색 원으로 표시
                surf = pygame.Surface((target_size, target_size), pygame.SRCALPHA)
                if code == 'N':
                    pygame.draw.circle(surf, (128, 128, 128), (target_size//2, target_size//2), BUBBLE_RADIUS)
                else:
                    pygame.draw.circle(surf, COLORS[code], (target_size//2, target_size//2), BUBBLE_RADIUS)
                self.bubble_images[code] = surf

        # --- 로고 이미지 로드 (크기 스케일링) ---
        self.map_editor_logo = None
        if ASSET_PATHS.get('map_editor_logo') and os.path.exists(ASSET_PATHS['map_editor_logo']):
            try:
                self.map_editor_logo = pygame.image.load(ASSET_PATHS['map_editor_logo']).convert_alpha()
                w = int(250 * SCALE)
                h = int(142 * SCALE)
                self.map_editor_logo = pygame.transform.smoothscale(self.map_editor_logo, (w, h))
            except:
                pass

        # --- 배경 이미지 로드 (화면 크기에 맞춰 스케일링) ---
        self.editor_bg = None
        if ASSET_PATHS.get('editor_bg') and os.path.exists(ASSET_PATHS['editor_bg']):
            try:
                self.editor_bg = pygame.image.load(ASSET_PATHS['editor_bg']).convert()
                self.editor_bg = pygame.transform.smoothscale(self.editor_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except:
                pass

        # --- 게임 영역 (bg_box) 계산 ---
        # CELL_SIZE는 이미 스케일링 된 값임
        map_pixel_width = (MAP_COLS * CELL_SIZE) + (CELL_SIZE // 2)
        
        # 오프셋 및 패딩에도 SCALE 적용
        self.grid_x_offset = ((SCREEN_WIDTH - map_pixel_width) // 2) + int(25 * SCALE)
        self.grid_y_offset = int(30 * SCALE)
        
        padding = int(10 * SCALE)
        game_area_w = map_pixel_width + (padding * 2)
        game_area_h = SCREEN_HEIGHT - self.grid_y_offset
        game_area_x = (SCREEN_WIDTH - game_area_w) // 2
        game_area_y = self.grid_y_offset - padding
        
        self.game_rect = pygame.Rect(game_area_x, game_area_y, game_area_w, game_area_h)
        self.grid = EditorGrid(self.grid_x_offset, self.grid_y_offset, self.bubble_images)
        
        # 캐논 위치
        cannon_x = self.game_rect.centerx
        cannon_y = self.game_rect.bottom - int(170 * SCALE) # 높이 오프셋 스케일링
        self.cannon = DecorCannon(cannon_x, cannon_y)
        self.game_over_line = self.cannon.y - CELL_SIZE * 0.5

        # --- UI 상태 변수 ---
        self.selected_brush = 'R'
        self.current_filename = "stage1.csv"
        self.file_list = []
        self.scroll_y = 0
        self.max_visible_files = 5
        self.item_height = int(90 * SCALE) # 아이템 높이 스케일링

        # 스크롤 바 드래그 관련 변수
        self.scrollbar_dragging = False
        self.scrollbar_rect = None

        self.save_msg_alpha = 0
        self.running = True  # 에디터 실행 상태

        self.refresh_file_list()
        self.create_ui_elements()
        
        if self.file_list:
            self.load_map(self.file_list[0])
        else:
            self.create_new_map()

    def create_ui_elements(self):
        """UI 요소 생성 (SCALE 적용)"""

        # ========================================
        # 좌측 팔레트 패널 (SCALE 적용)
        # ========================================
        panel_x = int(58 * SCALE)
        panel_y_start = int(283 * SCALE)
        panel_width = int(420 * SCALE)
        panel_height = int(591 * SCALE)

        self.left_panel_rect = pygame.Rect(panel_x, panel_y_start, panel_width, panel_height)

        # ========================================
        # 팔레트 버튼 (R, Y, B, G, N) - 2x3 그리드 (SCALE 적용)
        # ========================================
        self.palette_buttons = []
        colors_keys = ['R', 'Y', 'B', 'G', 'N']  # 장애물 'N' 추가

        # 패널 내부 상대 좌표
        start_x = self.left_panel_rect.x + int(107 * SCALE)
        start_y = self.left_panel_rect.y + int(170 * SCALE)
        gap = int(130 * SCALE)

        btn_size = int(70 * SCALE)

        for i, code in enumerate(colors_keys):
            bx = start_x + (i % 2) * gap
            by = start_y + (i // 2) * gap
            btn_img = self.bubble_images.get(code)
            
            # 버튼 이미지도 크기 조정 (필요하다면) - 현재는 버튼 클래스에서 rect 중앙에 원본 크기로 그림
            # 하지만 bubble_images는 이미 BUBBLE_RADIUS*2로 스케일링 되어있음 (OK)
            btn = Button(bx, by, btn_size, btn_size, "", lambda c=code: self.set_brush(c), image=btn_img)
            self.palette_buttons.append(btn)

        # 지우개 버튼
        erase_w = int(140 * SCALE)
        erase_h = int(50 * SCALE)
        erase_offset_y = int(350 * SCALE)
        
        erase_btn = Button(self.left_panel_rect.centerx - (erase_w // 2), start_y + erase_offset_y, 
                           erase_w, erase_h, "ERASE",
                           lambda: self.set_brush('.'), color=(100, 50, 50))
        self.palette_buttons.append(erase_btn)

        # ========================================
        # 하단 액션 버튼 (SCALE 적용)
        # ========================================
        self.action_buttons = []
        btn_width = int(100 * SCALE)
        btn_height = int(50 * SCALE)
        btn_y = SCREEN_HEIGHT - int(80 * SCALE)
        btn_gap = int(20 * SCALE)
        right_margin = int(34 * SCALE)

        # SAVE
        btn_save = Button(
            SCREEN_WIDTH - 3*btn_width - 2*btn_gap - right_margin,
            btn_y, btn_width, btn_height,
            "SAVE", self.save_current_map,
            color=(50, 150, 50)
        )

        # NEW
        btn_new = Button(
            SCREEN_WIDTH - 2*btn_width - 1*btn_gap - right_margin,
            btn_y, btn_width, btn_height,
            "NEW", self.create_new_map,
            color=(92, 226, 253)
        )

        # DELETE
        btn_delete = Button(
            SCREEN_WIDTH - 1*btn_width - right_margin,
            btn_y, btn_width, btn_height,
            "DELETE", self.delete_current_map,
            color=(150, 50, 50)
        )

        self.action_buttons.extend([btn_save, btn_new, btn_delete])

        # ========================================
        # 뒤로가기 버튼 (왼쪽 하단)
        # ========================================
        back_btn_width = int(140 * SCALE)
        back_btn_height = int(50 * SCALE)
        left_margin = int(34 * SCALE)
        
        btn_back = Button(
            left_margin,
            btn_y, back_btn_width, back_btn_height,
            "BACK (ESC)", self.exit_editor,
            color=(168, 212, 246)  # BTN_IDLE 색상과 동일
        )
        
        self.action_buttons.append(btn_back)

    # ... (refresh_file_list, set_brush, load_map, save_current_map, create_new_map, delete_current_map, update, handle_input 함수는 기존 로직과 동일하여 생략하지 않고 그대로 둡니다. handle_input에서 스크롤바 영역 계산에 SCALE 적용 필요) ...
    
    def refresh_file_list(self):
        folder = 'assets/map_data'
        if not os.path.exists(folder): os.makedirs(folder)
        files = [f for f in os.listdir(folder) if f.endswith('.csv')]
        def sort_key(f):
            try: return int(''.join(filter(str.isdigit, f)))
            except: return 0
        files.sort(key=sort_key)
        self.file_list = files

    def set_brush(self, color_code):
        self.selected_brush = color_code
    
    def exit_editor(self):
        """에디터 종료 (ESC 키와 동일한 효과)"""
        self.running = False

    def load_map(self, filename):
        self.current_filename = filename
        path = os.path.join('assets/map_data', filename)
        self.grid.map = [['.' for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                r = 0
                for row in reader:
                    if r >= MAP_ROWS: break
                    for c, cell in enumerate(row):
                        if c >= MAP_COLS: break
                        val = cell.strip().upper()
                        # 'N' (장애물)도 허용
                        if val in self.bubble_images or val == 'X':
                            self.grid.map[r][c] = val
                        else:
                            self.grid.map[r][c] = '.'
                    r += 1
        except Exception as e:
            print(f"Load failed: {e}")

    def save_current_map(self):
        folder = 'assets/map_data'
        if not os.path.exists(folder): os.makedirs(folder)
        path = os.path.join(folder, self.current_filename)
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for row in self.grid.map:
                    writer.writerow(row)
            print(f"Saved to {path}")
            self.save_msg_alpha = 255
        except Exception as e:
            print(f"Save failed: {e}")

    def create_new_map(self):
        folder = 'assets/map_data'
        if not os.path.exists(folder): os.makedirs(folder)
        max_num = 0
        for filename in self.file_list:
            try:
                num = int(''.join(filter(str.isdigit, filename)))
                max_num = max(max_num, num)
            except: pass
        next_num = max_num + 1
        new_filename = f"stage{next_num}.csv"
        path = os.path.join(folder, new_filename)
        empty_map = [['.' for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for row in empty_map:
                    writer.writerow(row)
            self.refresh_file_list()
            self.load_map(new_filename)
            try:
                new_index = self.file_list.index(new_filename)
                if new_index >= self.max_visible_files:
                    self.scroll_y = new_index - self.max_visible_files + 1
                else:
                    self.scroll_y = 0
            except ValueError:
                self.scroll_y = 0
        except Exception as e:
            print(f"Create failed: {e}")

    def delete_current_map(self):
        if not self.file_list: return
        try:
            current_index = self.file_list.index(self.current_filename)
        except ValueError:
            current_index = 0
        folder = 'assets/map_data'
        path = os.path.join(folder, self.current_filename)
        try:
            os.remove(path)
            self.refresh_file_list()
            if self.file_list:
                if current_index >= len(self.file_list):
                    next_index = len(self.file_list) - 1
                else:
                    next_index = current_index
                self.load_map(self.file_list[next_index])
                if next_index < self.scroll_y:
                    self.scroll_y = next_index
                elif next_index >= self.scroll_y + self.max_visible_files:
                    self.scroll_y = next_index - self.max_visible_files + 1
            else:
                self.create_new_map()
        except Exception as e:
            print(f"Delete failed: {e}")

    def update(self):
        if self.save_msg_alpha > 0:
            self.save_msg_alpha -= 4
            if self.save_msg_alpha < 0:
                self.save_msg_alpha = 0

    def handle_input(self):
        events = pygame.event.get()
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        # 스크롤바 위치 상수도 스케일링 필요
        right_panel_margin = int(479 * SCALE)
        right_x = SCREEN_WIDTH - right_panel_margin
        list_start_y = int(399 * SCALE)

        if self.scrollbar_dragging and mouse_pressed[0]:
            if self.scrollbar_rect and len(self.file_list) > self.max_visible_files:
                scrollbar_track_h = self.max_visible_files * self.item_height
                relative_y = mouse_pos[1] - list_start_y
                scroll_ratio = clamp(relative_y / scrollbar_track_h, 0, 1)
                max_scroll = len(self.file_list) - self.max_visible_files
                self.scroll_y = int(scroll_ratio * max_scroll)
        elif not mouse_pressed[0]:
            self.scrollbar_dragging = False

        if self.game_rect.collidepoint(mouse_pos) and not self.scrollbar_dragging:
            if mouse_pressed[0]:
                r, c = self.grid.screen_to_grid(*mouse_pos)
                if self.grid.is_in_bounds(r, c):
                    self.grid.set_cell(r, c, self.selected_brush)
            elif mouse_pressed[2]:
                r, c = self.grid.screen_to_grid(*mouse_pos)
                if self.grid.is_in_bounds(r, c):
                    self.grid.set_cell(r, c, '.')

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # ESC 키로 에디터 종료 (메뉴로 돌아가기)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

            if event.type == pygame.MOUSEWHEEL:
                if len(self.file_list) > self.max_visible_files:
                    self.scroll_y -= event.y
                    max_scroll = len(self.file_list) - self.max_visible_files
                    self.scroll_y = clamp(self.scroll_y, 0, max_scroll)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.scrollbar_rect and self.scrollbar_rect.collidepoint(event.pos):
                    self.scrollbar_dragging = True

            for btn in self.palette_buttons: btn.handle_event(event)
            for btn in self.action_buttons: btn.handle_event(event)

            # 우측 패널 선택 영역도 스케일링 (패널 내부 좌표 기준 오프셋 적용)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 1. 리스트가 시작되는 정확한 Y 좌표 (draw_ui의 list_start_y와 일치)
                list_start_y = int(399 * SCALE)

                # 2. 리스트 영역의 높이 계산 (아이템 높이 * 보이는 개수)
                list_area_height = self.max_visible_files * self.item_height

                # 3. 우측 패널 X 시작 좌표 재계산 (혹시 변수가 scope 밖에 있을 경우 대비)
                right_panel_margin = int(479 * SCALE)
                right_x = SCREEN_WIDTH - right_panel_margin

                # 4. 클릭 판정: Y좌표가 [리스트 시작점] ~ [리스트 끝점] 사이인지 확인
                if mouse_pos[0] > right_x and list_start_y <= mouse_pos[1] < list_start_y + list_area_height:
                    # 마우스 Y좌표에서 시작 오프셋을 뺀 값으로 인덱스 계산
                    relative_y = mouse_pos[1] - list_start_y
                    idx = int(relative_y // self.item_height) + self.scroll_y
                    
                    if 0 <= idx < len(self.file_list):
                        self.load_map(self.file_list[idx])

    def draw_ui(self):
        """UI 렌더링 (SCALE 적용)"""
        # 배경 이미지가 있으면 배경 이미지 사용, 없으면 기본 배경색
        if self.editor_bg:
            self.screen.blit(self.editor_bg, (0, 0))
        else:
            self.screen.fill(THEME_BG)

        # 1. 게임 영역
        pygame.draw.rect(self.screen, (0, 100, 200), self.game_rect)

        # 2. 게임 오버 라인
        line_w = max(1, int(10 * SCALE))
        pygame.draw.line(self.screen, (0, 255, 3),
                         (self.game_rect.left, self.game_over_line),
                         (self.game_rect.right, self.game_over_line), line_w)

        # 3. 캐논 & 그리드
        self.cannon.draw(self.screen)
        self.grid.draw(self.screen)

        # 4. 좌측 팔레트 패널
        border_radius = int(15 * SCALE)
        border_width = max(1, int(10 * SCALE)) # 너무 얇아지지 않게 max
        pygame.draw.rect(self.screen, THEME_PANEL, self.left_panel_rect, border_radius=border_radius)
        pygame.draw.rect(self.screen, THEME_BORDER, self.left_panel_rect, border_width, border_radius=border_radius)

        # 타이틀 & 로고 위치
        logo_x = int(50 * SCALE)
        logo_y = int(60 * SCALE)
        title_x = int(30 * SCALE)
        title_y = int(50 * SCALE)

        if self.map_editor_logo:
            self.screen.blit(self.map_editor_logo, (logo_x, logo_y))
        else:
            title_surf = self.font_title.render("MAP EDITOR", True, (255, 255, 255))
            self.screen.blit(title_surf, (title_x, title_y))

        # PALETTE 라벨
        label_offset_x = int(80 * SCALE)
        label_offset_y = int(70 * SCALE)
        palette_txt = self.font_title.render("Bubble : ", True, THEME_BORDER)
        self.screen.blit(palette_txt, (self.left_panel_rect.x + label_offset_x, self.left_panel_rect.y + label_offset_y))

        # 현재 브러쉬
        cur_img = self.bubble_images.get(self.selected_brush)
        brush_offset_x = int(70 * SCALE)
        brush_offset_y = int(80 * SCALE)
        
        if cur_img:
            rect = cur_img.get_rect(center=(self.left_panel_rect.centerx + brush_offset_x, self.left_panel_rect.y + brush_offset_y))
            self.screen.blit(cur_img, rect)
        elif self.selected_brush == '.':
            e_txt = self.font_ui.render("ERASER", True, (200, 200, 200))
            e_rect_offset_x = int(250 * SCALE)
            e_rect_offset_y = int(80 * SCALE)
            self.screen.blit(e_txt, (self.left_panel_rect.x + e_rect_offset_x, self.left_panel_rect.y + e_rect_offset_y))

        for btn in self.palette_buttons: btn.draw(self.screen, self.font_ui)

        # 5. 우측 패널 (SCALE 적용)
        right_panel_margin = int(479 * SCALE)
        right_x = SCREEN_WIDTH - right_panel_margin
        right_panel_y = int(283 * SCALE)
        right_panel_width = int(420 * SCALE)
        list_start_y = int(399 * SCALE)

        visible_count = min(len(self.file_list), self.max_visible_files)
        panel_height = int(591 * SCALE)

        pygame.draw.rect(self.screen, THEME_PANEL,
                        (right_x, right_panel_y, right_panel_width, panel_height),
                        border_radius=border_radius)
        pygame.draw.rect(self.screen, THEME_BORDER,
                        (right_x, right_panel_y, right_panel_width, panel_height),
                        max(1, int(15 * SCALE)), border_radius=border_radius)

        st_title_offset_x = int(140 * SCALE)
        st_title_offset_y = int(350 * SCALE)
        st_title = self.font_title.render("STAGES", True, THEME_BORDER)
        self.screen.blit(st_title, (right_x + st_title_offset_x, st_title_offset_y))

        # 5-1. 리스트 아이템
        item_margin = int(20 * SCALE)
        item_width = int(285 * SCALE)
        item_left_margin = int(72 * SCALE)

        for i in range(self.max_visible_files):
            idx = i + self.scroll_y
            if idx >= len(self.file_list): break
            filename = self.file_list[idx]

            item_y = list_start_y + (i * self.item_height) + item_margin
            item_rect = pygame.Rect(right_x + item_left_margin, item_y,
                                   item_width, self.item_height - item_margin * 2)

            radius_sm = int(5 * SCALE)
            if filename == self.current_filename:
                pygame.draw.rect(self.screen, BTN_HOVER, item_rect, border_radius=radius_sm)
                pygame.draw.rect(self.screen, (255, 255, 0), item_rect, max(1, int(2*SCALE)), border_radius=radius_sm)
            else:
                pygame.draw.rect(self.screen, BTN_IDLE, item_rect, border_radius=radius_sm)

            display_name = filename.replace('.csv', '').upper()
            txt = self.font_ui.render(display_name, True, (0,0,0)) # 리스트 텍스트 검정
            txt_rect = txt.get_rect(center=item_rect.center)
            self.screen.blit(txt, txt_rect)

        # 5-2. 스크롤바
        if len(self.file_list) > self.max_visible_files:
            scrollbar_offset_x = int(380 * SCALE)
            scrollbar_x = right_x + scrollbar_offset_x
            scrollbar_track_y = list_start_y
            scrollbar_track_h = self.max_visible_files * self.item_height
            scrollbar_w = int(8 * SCALE)

            pygame.draw.rect(self.screen, (30, 40, 60),
                           (scrollbar_x, scrollbar_track_y, scrollbar_w, scrollbar_track_h),
                           border_radius=int(4*SCALE))

            max_scroll = len(self.file_list) - self.max_visible_files
            handle_ratio = self.max_visible_files / len(self.file_list)
            min_handle_h = int(30 * SCALE)
            handle_h = max(min_handle_h, int(scrollbar_track_h * handle_ratio))

            scroll_ratio = self.scroll_y / max_scroll if max_scroll > 0 else 0
            handle_y = scrollbar_track_y + int((scrollbar_track_h - handle_h) * scroll_ratio)

            self.scrollbar_rect = pygame.Rect(scrollbar_x, handle_y, scrollbar_w, handle_h)
            pygame.draw.rect(self.screen, THEME_BORDER, self.scrollbar_rect, border_radius=int(4*SCALE))
        else:
            self.scrollbar_rect = None

        # 6. 하단 버튼
        for btn in self.action_buttons: btn.draw(self.screen, self.font_ui)

        # 7. 정보 텍스트
        bottom_offset = int(30 * SCALE)
        file_info = self.font_ui.render(f"EDITING: {self.current_filename}", True, (150, 150, 150))
        self.screen.blit(file_info, file_info.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - bottom_offset)))

        # 8. Saved 메시지
        if self.save_msg_alpha > 0:
            msg_surf = self.font_big.render("SAVED!", True, (100, 255, 100))
            msg_surf.set_alpha(self.save_msg_alpha)
            rect = msg_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))

            bg_pad_w = int(40 * SCALE)
            bg_pad_h = int(20 * SCALE)
            bg_rect = rect.inflate(bg_pad_w, bg_pad_h)
            bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            bg_surf.fill((0, 0, 0, int(self.save_msg_alpha * 0.7)))

            self.screen.blit(bg_surf, bg_rect)
            self.screen.blit(msg_surf, rect)

    def run(self):
        while self.running:
            self.update()
            self.handle_input()
            self.draw_ui()
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    editor = MapEditor()
    editor.run()