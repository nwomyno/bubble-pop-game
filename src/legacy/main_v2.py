import math
import random
import sys
import csv
import os
from typing import List, Set, Tuple, Optional

import pygame

# 메뉴 UI
from scene_manager import SceneManager
from menu_scene import MenuScene

# 설정 파일, 모듈들
from config import (
    SCREEN_WIDTH,SCREEN_HEIGHT,FPS,CELL_SIZE,BUBBLE_RADIUS,BUBBLE_SPEED,
    LAUNCH_COOLDOWN,WALL_DROP_PIXELS,MAP_ROWS,MAP_COLS,
    NEXT_BUBBLE_X,NEXT_BUBBLE_Y_OFFSET
)
from game_settings import (
    END_SCREEN_DELAY,POP_SOUND_VOLUME,TAP_SOUND_VOLUME
)
from asset_paths import ASSET_PATHS
from constants import BubbleColor, GameState
from color_settings import (COLORS,
                            COLOR_MAP)

# ─────────────────────────────────────────
# 상대 경로 문제 해결
# ─────────────────────────────────────────
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

# --- 에셋 파일 경로 ---  (<-- 추가됨)
# 사용자의 실제 파일 경로로 수정하세요.
# ASSET_PATHS = {
#     'bubble_red': 'assets/images/bubble_red.png',
#     'bubble_yellow': 'assets/images/bubble_yellow.png',
#     'bubble_blue': 'assets/images/bubble_blue.png',
#     'bubble_green': 'assets/images/bubble_green.png',
#     'background': 'assets/images/background.png',
#     'char_left': 'assets/images/char_left.png',
#     'char_right': 'assets/images/char_right.png',
#     'logo': 'assets/images/logo.png',
#     'cannon_arrow': 'assets/images/cannon_arrow.png', # 십자+화살표 이미지
#     'font': None,  # None으로 설정 시 기본 폰트 사용, 'assets/pixel_font.ttf' 등으로 변경 가능
#     'bgm': 'assets/sounds/main_theme_01.wav',  # 배경음악
#     'pop_sounds': [  # 터트릴 때 재생할 효과음 리스트
#         'assets/sounds/pop_01.wav',
#         'assets/sounds/pop_02.wav',
#     ],
#     'tap_sound': 'assets/sounds/tap.wav',  # 달라붙을 때 재생할 효과음
# }

# 게임 초기화 [수정: main()에 옮김.]
# pygame.init()
# pygame.mixer.init()  # 사운드 시스템 초기화

# 버블 이미지 로드
try:
    BUBBLE_IMAGES: dict[str, pygame.Surface] = {
        'R': pygame.image.load(ASSET_PATHS['bubble_red']),
        'Y': pygame.image.load(ASSET_PATHS['bubble_yellow']),
        'B': pygame.image.load(ASSET_PATHS['bubble_blue']),
        'G': pygame.image.load(ASSET_PATHS['bubble_green']),
    }
    print("버블 이미지 로드 완료.")
except pygame.error as e:
    print(f"이미지 로드 실패함: {e}. 기본 색상으로 대체합니다.")
    BUBBLE_IMAGES = None

# ======== 전역 설정 ========
    # → config.py로 분리
# SCREEN_WIDTH: int = 1920
# SCREEN_HEIGHT: int = 1080
# FPS: int = 60

    # → game_settings.py로 분리
# UI_ALPHA = 180
# END_SCREEN_DELAY = 300

# 사운드 볼륨 설정 (0.0 ~ 1.0)
# POP_SOUND_VOLUME = 0.3  # 터트릴 때 효과음 볼륨
# TAP_SOUND_VOLUME = 0.4  # 달라붙을 때 효과음 볼륨

# 다음 버블 미리보기 표시 좌표 (사용자가 설정 가능)
# NEXT_BUBBLE_X = 750  # 다음 버블 표시 X 좌표
# NEXT_BUBBLE_Y_OFFSET = -80  # SCREEN_HEIGHT 기준 Y 오프셋 (음수면 하단에서 위로)

# CELL_SIZE: int = 100
# BUBBLE_RADIUS: int = 47
# BUBBLE_SPEED: int = 30

# ======== 이미지 크기 조정 ========
if BUBBLE_IMAGES:
    target_size = BUBBLE_RADIUS * 2
    for color in BUBBLE_IMAGES:
        BUBBLE_IMAGES[color] = pygame.transform.smoothscale(
            BUBBLE_IMAGES[color],
            (target_size, target_size)
        )
    print(f"버블 이미지 크기 조정 완료: {target_size}x{target_size}px")

# LAUNCH_COOLDOWN: int = 4
# WALL_DROP_PIXELS: int = CELL_SIZE

# → color_settings.py로 분리
COLORS: dict[str, Tuple[int, int, int]] = {
    'R': (220, 50, 50),
    'Y': (240, 200, 60),
    'B': (60, 100, 240),
    'G': (70, 200, 120),
}

# 맵 크기
# MAP_ROWS: int = 6
# MAP_COLS: int = 8

# STAGES: List[List[List[str]]] = [
#     # 스테이지 1
#     [
#         list("RRYYGGBBRRYY"),
#         list("RRYYGGBBRRYG"), # / 대신 G로 채움
#         list("BBGGRRYYBBGG"),
#         list("BBGGRRYYBBGR"), # / 대신 R로 채움
#         list("............"),
#         list("............"),
#         list("............"),
#         list("............"),
#         list("............"),
#         list("............"),
#     ],
#     # 스테이지 2
#     [
#         list("R.Y.G.B.R.Y."),
#         list("Y.G.B.R.Y.G."),
#         list("G.B.R.Y.G.B."),
#         list("B.R.Y.G.B.R."),
#         list("....RRGGYYBB"),
#         list("....RRGGYYBB"),
#         list("............"),
#         list("............"),
#         list("............"),
#         list("............"),
#     ],
# ]

# ======== 유틸리티 함수 정의 ========
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def load_stage_from_csv(stage_index: int) -> List[List[str]]:
    """CSV 파일에서 스테이지 맵 데이터를 읽어옴.

    Args:
        stage_index: 스테이지 인덱스 (0부터 시작)

    Returns:
        맵 데이터 리스트 (각 행은 문자열 리스트)
    """
    csv_path = f'assets/map_data/stage{stage_index + 1}.csv'

    # 파일이 존재하는지 확인
    if not os.path.exists(csv_path):
        print(f"경고: {csv_path} 파일을 찾을 수 없습니다. 기본 맵을 사용합니다.")
        # 기본 빈 맵 반환
        return [['.' for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]

    stage_map = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                # CSV 행을 리스트로 변환
                map_row = []
                for cell in row:
                    cell = cell.strip()  # 공백 제거
                    # 빈 값이나 'X'는 '.'으로 변환
                    if cell == '' or cell.upper() == 'X':
                        map_row.append('.')
                    elif cell.upper() in COLORS:
                        map_row.append(cell.upper())
                    else:
                        map_row.append('.')  # 알 수 없는 값은 빈 칸으로

                # 행의 길이가 MAP_COLS보다 짧으면 '.'으로 채움
                while len(map_row) < MAP_COLS:
                    map_row.append('.')
                # 행의 길이가 MAP_COLS보다 길면 자름
                map_row = map_row[:MAP_COLS]

                stage_map.append(map_row)

        # 행의 개수가 MAP_ROWS보다 짧으면 빈 행으로 채움
        while len(stage_map) < MAP_ROWS:
            stage_map.append(['.' for _ in range(MAP_COLS)])
        # 행의 개수가 MAP_ROWS보다 길면 자름
        stage_map = stage_map[:MAP_ROWS]

        print(f"스테이지 {stage_index + 1} 맵 데이터 로드 완료: {csv_path}")
        return stage_map

    except Exception as e:
        print(f"오류: {csv_path} 파일을 읽는 중 오류가 발생했습니다: {e}")
        # 기본 빈 맵 반환
        return [['.' for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]

# ======== 버블 클래스 - 버블 객체 ========
class Bubble:
    """ 게임의 각 버블을 표현함. 버블의 위치, 색깔, 상태를 관리하고 화면에 그림. """
    def __init__(self, x: float, y: float, color: str, radius: int = BUBBLE_RADIUS) -> None:
        self.x: float = x
        self.y: float = y
        self.color: str = color
        self.radius: int = radius
        self.in_air: bool = False
        self.is_attached: bool = False
        self.angle_degree: float = 90
        self.speed: int = BUBBLE_SPEED
        self.row_idx: int = -1
        self.col_idx: int = -1

    def draw(self, screen: pygame.Surface) -> None:
        if BUBBLE_IMAGES:
            img = BUBBLE_IMAGES[self.color]
            rect = img.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(img, rect)
        else:
            pygame.draw.circle(screen, COLORS[self.color], (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.radius, 2)

    def set_angle(self, angle_degree: float) -> None:
        self.angle_degree = angle_degree

    def set_grid_index(self, r: int, c: int) -> None:
        self.row_idx = r
        self.col_idx = c

    def move(self) -> None:
        rad = math.radians(self.angle_degree)
        dx = self.speed * math.cos(rad)
        dy = -self.speed * math.sin(rad)
        self.x += dx
        self.y += dy

        # (<-- 수정됨) 벽 충돌을 게임 영역 기준으로 변경
        grid_x_start = (SCREEN_WIDTH - (MAP_COLS * CELL_SIZE)) // 2
        grid_x_end = grid_x_start + (MAP_COLS * CELL_SIZE)

        if self.x - self.radius < grid_x_start:
            self.x = grid_x_start + self.radius
            self.angle_degree = 180 - self.angle_degree
        elif self.x + self.radius > grid_x_end:
            self.x = grid_x_end - self.radius
            self.angle_degree = 180 - self.angle_degree


# ======== Cannon 클래스: 발사대 ========
class Cannon:
    """ 버블을 발사하는 발사대 정의. 각도 조정, 조준선을 화면에 그리는 역할. """
    def __init__(self, x: int, y: int) -> None:
        self.x: int = x
        self.y: int = y
        self.angle: float = 90
        self.min_angle: float = 10
        self.max_angle: float = 170
        self.angle_speed: float = 4.0  # 회전 속도 증가 (2.0 -> 4.0)

            # --- 그래픽 로드 --- (<-- 추가됨)
        try:
            # self.base_image = pygame.image.load(ASSET_PATHS['cannon_base']).convert_alpha() # (<-- 삭제됨)
            self.arrow_image = pygame.image.load(ASSET_PATHS['cannon_arrow']).convert_alpha()

            # (예시 크기 조절, 필요에 따라 수정)
            # self.base_image = pygame.transform.smoothscale(self.base_image, (90, 90)) # (<-- 삭제됨)
            # 십자선+화살표 이미지 크기를 90x90으로 가정, 필요시 수정
            self.arrow_image = pygame.transform.smoothscale(self.arrow_image, (152, 317)) # (<-- 크기 수정)

        except pygame.error:
            print("발사대 이미지 로드 실패")
            self.arrow_image = None

    def rotate(self, delta: float) -> None:
        self.angle += delta
        self.angle = clamp(self.angle, self.min_angle, self.max_angle)

    def draw(self, screen: pygame.Surface) -> None:
        # --- 이미지 기반 그리기 --- (<-- 수정됨)
        if self.arrow_image: # (<-- base_image에서 arrow_image로 조건 변경)

            # 2. 화살표/십자선 회전 및 그리기
            # Pygame은 0도가 오른쪽이므로, 90도를 빼서 위쪽(90도)을 기준으로 만듭니다.
            rotated_arrow = pygame.transform.rotate(self.arrow_image, self.angle - 90)
            arrow_rect = rotated_arrow.get_rect(center=(self.x, self.y))

            screen.blit(rotated_arrow, arrow_rect)

        else: # 이미지가 없을 경우의 대체
            length = 100
            rad = math.radians(self.angle)
            end_x = self.x + length * math.cos(rad)
            end_y = self.y - length * math.sin(rad)
            pygame.draw.line(screen, (255, 255, 255), (self.x, self.y), (end_x, end_y), 4)
            pygame.draw.circle(screen, (255, 0, 0), (self.x, self.y), 6)


# ======== HexGrid 클래스 - 육각형 격자 체계 ========
class HexGrid:
    """ 육각형 모양 배열의 버블 격자를 관리함. """
    # --- 오프셋 추가 --- (<-- 수정됨)
    def __init__(self, rows: int, cols: int, cell_size: int, wall_offset: int = 0,
                 x_offset: int = 0, y_offset: int = 0) -> None:
        self.rows: int = rows
        self.cols: int = cols
        self.cell: int = cell_size
        self.wall_offset: int = wall_offset
        self.x_offset: int = x_offset # (<-- 추가됨)
        self.y_offset: int = y_offset # (<-- 추가됨)
        self.map: List[List[str]] = [['.' for _ in range(cols)] for _ in range(rows)]
        self.bubble_list: List[Bubble] = []

    def load_from_stage(self, stage_map: List[List[str]]) -> None:
        self.map = [row[:] for row in stage_map]
        self.bubble_list = []

        for r in range(self.rows):
            # 맵 데이터가 실제 행보다 짧을 경우를 대비 (<-- 수정됨)
            if r >= len(self.map):
                break
            for c in range(self.cols):
                if c < len(self.map[r]):
                    ch = self.map[r][c]
                else:
                    ch = '.'

                if ch in COLORS:
                    x, y = self.get_cell_center(r, c)
                    b = Bubble(x, y, ch)
                    b.is_attached = True
                    b.set_grid_index(r, c)
                    self.bubble_list.append(b)

    def get_cell_center(self, r: int, c: int) -> Tuple[int, int]:
        # --- 오프셋 적용 --- (<-- 수정됨)
        x = c * self.cell + self.cell // 2 + self.x_offset
        y = r * self.cell + self.cell // 2 + self.wall_offset + self.y_offset

        if r % 2 == 1:
            x += self.cell // 2
        return x, y

    def screen_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        # --- 오프셋 적용 --- (<-- 수정됨)
        r = int((y - self.wall_offset - self.y_offset) // self.cell)
        if r < 0:
            r = 0

        c_base = x - self.x_offset
        if r % 2 == 1:
            c = int((c_base - self.cell // 2) // self.cell)
        else:
            c = int(c_base // self.cell)

        c = clamp(c, 0, self.cols - 1)
        r = clamp(r, 0, self.rows - 1)
        return r, c

    def place_bubble(self, bubble: Bubble, r: int, c: int) -> None:
        # ' / ' 문자 처리를 위한 임시 방편 (<-- 수정됨)
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            print(f"Error: Out of bounds placement at ({r}, {c})")
            return

        if self.map[r][c] == '/':
            c = clamp(c + 1, 0, self.cols - 1)

        # 맵 데이터가 짧을 경우 대비
        if r >= len(self.map) or c >= len(self.map[r]):
             print(f"Warning: Placing bubble at ({r},{c}) which may be out of map data bounds.")
             # 필요시 self.map 크기를 동적으로 늘리는 로직 추가

        self.map[r][c] = bubble.color
        cx, cy = self.get_cell_center(r, c)
        bubble.x, bubble.y = cx, cy
        bubble.is_attached = True
        bubble.in_air = False
        bubble.set_grid_index(r, c)
        self.bubble_list.append(bubble)

    def nearest_grid_to_point(self, x: float, y: float) -> Tuple[int, int]:
        r, c = self.screen_to_grid(x, y)

        if not self.is_in_bounds(r, c):
             return (0, clamp(c, 0, self.cols-1)) # 최상단으로 강제

        if self.map[r][c] in COLORS or self.map[r][c] == '/':
            neighbors = self.get_neighbors(r, c)

            # 가장 가까운 빈 이웃 찾기 (거리 기반) (<-- 로직 개선)
            best_neighbor = (r, c) # 기본값
            min_dist_sq = float('inf')

            found_empty = False
            for nr, nc in neighbors:
                if self.is_in_bounds(nr, nc) and self.map[nr][nc] == '.':
                    nx, ny = self.get_cell_center(nr, nc)
                    dist_sq = (x - nx)**2 + (y - ny)**2
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        best_neighbor = (nr, nc)
                        found_empty = True

            if found_empty:
                return best_neighbor

        # 현재 셀이 비어있으면 그대로 반환
        if self.is_in_bounds(r,c) and self.map[r][c] == '.':
            return r, c

        # 모든 이웃이 찼거나 비어있는 이웃이 없으면, 현재 위치 반환 (강제 배치)
        print(f"Warning: no empty cell found near. ({r},{c}). Forcing.")
        return r,c


    def is_in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def get_neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        if r % 2 == 0:
            dr = [0, -1, -1, 0, 1, 1]
            dc = [-1, -1, 0, 1, 0, -1]
        else:
            dr = [0, -1, -1, 0, 1, 1]
            dc = [-1, 0, 1, 1, 1, 0]
        return [(r + dr[i], c + dc[i]) for i in range(6)]

    def dfs_same_color(self, row: int, col: int, color: str, visited: Set[Tuple[int, int]]) -> None:
        stack = [(row, col)]
        while stack:
            r, c = stack.pop()
            if not self.is_in_bounds(r, c) or (r, c) in visited:
                continue

            # 맵 데이터가 짧을 경우 대비
            if r >= len(self.map) or c >= len(self.map[r]):
                continue

            if self.map[r][c] != color:
                continue

            visited.add((r, c))
            for nr, nc in self.get_neighbors(r, c):
                stack.append((nr, nc))

    def remove_cells(self, cells: Set[Tuple[int, int]]) -> None:
        cell_set = set(cells)
        for (r, c) in cell_set:
            if self.is_in_bounds(r, c): # (<-- 안정성 추가)
                self.map[r][c] = '.'
        self.bubble_list = [
            b for b in self.bubble_list
            if (b.row_idx, b.col_idx) not in cell_set
        ]

    def flood_from_top(self) -> Set[Tuple[int, int]]:
        visited: Set[Tuple[int, int]] = set()
        for c in range(self.cols):
            # 맵 데이터가 짧을 경우 대비
            if 0 < len(self.map) and c < len(self.map[0]):
                if self.map[0][c] in COLORS:
                    self._dfs_reachable(0, c, visited)
        return visited

    def _dfs_reachable(self, row: int, col: int, visited: Set[Tuple[int, int]]) -> None:
        if not self.is_in_bounds(row, col) or (row, col) in visited:
            return

        # 맵 데이터가 짧을 경우 대비
        if row >= len(self.map) or col >= len(self.map[row]):
            return

        if self.map[row][col] not in COLORS:
            return

        visited.add((row, col))
        for nr, nc in self.get_neighbors(row, col):
            self._dfs_reachable(nr, nc, visited)

    def remove_hanging(self) -> None:
        connected = self.flood_from_top()
        not_connected: List[Tuple[int, int]] = []
        for r in range(self.rows):
            # 맵 데이터가 짧을 경우 대비
            if r >= len(self.map):
                break
            for c in range(self.cols):
                if c >= len(self.map[r]):
                    break
                if self.map[r][c] in COLORS and (r, c) not in connected:
                    not_connected.append((r, c))
        if not_connected:
            self.remove_cells(set(not_connected))

    def draw(self, screen: pygame.Surface) -> None:
        for b in self.bubble_list:
            b.draw(screen)

    def drop_wall(self) -> None:
        self.wall_offset += WALL_DROP_PIXELS
        for b in self.bubble_list:
            cx, cy = self.get_cell_center(b.row_idx, b.col_idx)
            b.x, b.y = cx, cy

# ======== ScoreDisplay 클래스 - 점수 표시 ========
class ScoreDisplay:
    """ 게임의 현재 점수를 표시하는 UI. """
    def __init__(self) -> None:
        self.score: int = 0
        # --- 폰트 수정 --- (<-- 수정됨)
        try:
            self.font = pygame.font.Font(ASSET_PATHS['font'], 50)
        except:
            print("픽셀 폰트 로드 실패. 기본 폰트로 대체합니다.")
            self.font = pygame.font.Font(None, 50) # 크기 키움

    def add(self, points: int) -> None:
        self.score += points

    # --- 레벨 표시 추가 --- (<-- 수정됨)
    def draw(self, screen: pygame.Surface, level: int) -> None:
        # 스크린샷과 같이 검은색 텍스트 사용
        score_txt = self.font.render(f'SCORE : {self.score}', True, (0, 0, 0))
        level_txt = self.font.render(f'LEVEL : {level}', True, (0, 0, 0))

        # 배경 제거, 위치 변경
        screen.blit(score_txt, (30, 30))
        screen.blit(level_txt, (30, 80))


# ======== Game 클래스 - 메인 게임 로직 ========
class Game:
    """ 게임의 전체 로직을 관리하는 메인 클래스임. """
    def __init__(self) -> None:
        self.screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Bubble Pop (K-Univ. Edition)") # (<-- 수정됨)
        self.clock: pygame.time.Clock = pygame.time.Clock()

        # --- 레이아웃 오프셋 계산 --- (<-- 추가됨)
        # FIXME: 레이아웃 계산 개선
        # 맵의 실제 너비를 계산
        map_pixel_width = (MAP_COLS * CELL_SIZE) + (CELL_SIZE // 2)
        self.grid_x_offset = ((SCREEN_WIDTH - map_pixel_width) // 2) + 25
            # [수정: 미세 왼쪽 이동]
        # self.grid_x_offset = (SCREEN_WIDTH-map_pixel_width)//2 -10
        self.grid_y_offset = 30 # 상단 여백
            # [수정: 상단 여백 늘리기]
        # self.grid_y_offset = 70

        # FIXME: 게임 영역 사각형 계산 재조정
        # 파란색 게임 영역 사각형 정의
        padding = 10
            # [수정: 패딩 증가]
        # padding = 20
        game_area_w = map_pixel_width + (padding * 2)
        game_area_h = SCREEN_HEIGHT - self.grid_y_offset  # 하단 여백 50
        # game_area_h = SCREEN_HEIGHT - self.grid_y_offset-100
            # [수정: 하단 여백 추가]
        game_area_x = (SCREEN_WIDTH - game_area_w) // 2
        game_area_y = self.grid_y_offset - padding
        self.game_rect = pygame.Rect(game_area_x, game_area_y, game_area_w, game_area_h)

        # FIXME: 초기화 세부 조정
        # --- HexGrid 초기화 수정 --- (<-- 수정됨)
        self.grid: HexGrid = HexGrid(MAP_ROWS, MAP_COLS, CELL_SIZE,
                                     0, # wall_offset
                                     self.grid_x_offset, self.grid_y_offset)
        # self.grid: HexGrid = HexGrid(MAP_ROWS, MAP_COLS, CELL_SIZE,
        #                              0, # wall_offset
        #                              self.grid_x_offset-10, self.grid_y_offset+10)
            # [수정: x 오프셋, y 오프셋 미세 조정]

        # FIXME: 발사대 위치 미세 조정
        # --- 발사대 위치 수정 --- (<-- 수정됨)
        cannon_x = self.game_rect.centerx
        cannon_y = self.game_rect.bottom - 170  # 게임 영역 하단에서 60px 위
        # cannon_y = self.game_rect.bottom - 200
            # [수정: 게임 영역 하단에서 더 높게 조정]
#         cannon_y = self.game_rect.bottom - 120  # 게임 영역 하단에서 60px 위
        self.cannon: Cannon = Cannon(cannon_x, cannon_y)

        # --- 게임 오버 라인 수정 --- (<-- 수정됨)
        self.game_over_line = self.cannon.y - CELL_SIZE * 0.5
        # self.game_over_line = self.cannon.y - CELL_SIZE * 0.7

        self.score_ui: ScoreDisplay = ScoreDisplay()

        # --- 배경 및 UI 이미지 로드 --- (<-- 추가됨)
        try:
            self.background_image = pygame.image.load(ASSET_PATHS['background']).convert()
            self.background_image = pygame.transform.scale(self.background_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

            self.char_left = pygame.image.load(ASSET_PATHS['char_left']).convert_alpha()
            self.char_right = pygame.image.load(ASSET_PATHS['char_right']).convert_alpha()
            self.logo = pygame.image.load(ASSET_PATHS['logo']).convert_alpha()

            # (예시 크기 조절, 필요에 따라 수정)
            self.char_left = pygame.transform.smoothscale(self.char_left, (313, 546))
            self.char_right = pygame.transform.smoothscale(self.char_right, (308, 555))
            self.logo = pygame.transform.smoothscale(self.logo, (176, 176))

#             # (<-- 추가됨) 게임 영역 배경 이미지 로드
#             self.game_area_bg = pygame.image.load(ASSET_PATHS['game_area_bg']).convert_alpha()
#             # 원본 크기 사용, 앵커(중심)만 self.game_rect의 중심으로 설정
#             self.game_area_bg_rect = self.game_area_bg.get_rect(center=self.game_rect.center)

        except pygame.error as e:
            print(f"배경/UI 이미지 로드 실패: {e}")
            self.background_image = None
            self.char_left = None
            self.char_right = None
            self.logo = None

        # --- 사운드 로드 및 재생 --- (<-- 추가됨)
        try:
            # BGM 로드 및 무한 반복 재생
            pygame.mixer.music.load(ASSET_PATHS['bgm'])
            pygame.mixer.music.set_volume(0.1)  # 볼륨 설정 (0.0 ~ 1.0)
            pygame.mixer.music.play(-1)  # -1은 무한 반복
            print("BGM 재생 시작")
        except pygame.error as e:
            print(f"BGM 로드 실패: {e}")

        # 효과음 리스트 로드 (터트릴 때)
        self.pop_sounds = []
        for sound_path in ASSET_PATHS['pop_sounds']:
            try:
                sound = pygame.mixer.Sound(sound_path)
                sound.set_volume(POP_SOUND_VOLUME)  # 볼륨 설정
                self.pop_sounds.append(sound)
            except pygame.error as e:
                print(f"효과음 로드 실패: {sound_path} - {e}")

        if not self.pop_sounds:
            print("경고: 효과음 파일을 찾을 수 없습니다.")

        # 달라붙을 때 효과음 로드
        try:
            self.tap_sound = pygame.mixer.Sound(ASSET_PATHS['tap_sound'])
            self.tap_sound.set_volume(TAP_SOUND_VOLUME)  # 볼륨 설정
        except pygame.error as e:
            print(f"tap 효과음 로드 실패: {ASSET_PATHS['tap_sound']} - {e}")
            self.tap_sound = None

        # 게임 상태
        self.current_stage: int = 0
        self.current_bubble: Optional[Bubble] = None
        self.next_bubble: Optional[Bubble] = None
        self.fire_in_air: bool = False
        self.fire_count: int = 0
        self.running: bool = True

        self.load_stage(self.current_stage)

    def load_stage(self, stage_index: int) -> None:
        # CSV 파일에서 맵 데이터 읽어오기
        stage_map = load_stage_from_csv(stage_index)

        # 맵이 비어있으면 게임 종료
        if not stage_map or all(all(cell == '.' for cell in row) for row in stage_map):
            # 다음 스테이지 파일이 있는지 확인
            next_csv_path = f'assets/map_data/stage{stage_index + 2}.csv'
            if not os.path.exists(next_csv_path):
                self.running = False  # 모든 스테이지 클리어
                return

        # --- 오프셋 초기화 시 y_offset도 반영 --- (<-- 수정됨)
        self.grid.wall_offset = 0
        self.grid.y_offset = self.grid_y_offset # y_offset 재설정

        self.grid.load_from_stage(stage_map)

        self.current_bubble = None
        self.next_bubble = None
        self.fire_in_air = False
        self.fire_count = 0

        self.prepare_bubbles()

    def random_color_from_map(self) -> str:
        # 현재 맵에 남아있는 버블들의 색깔만 수집함.
        colors = set()
        # grid.bubble_list에서 실제 남아있는 버블들의 색을 수집함.
        for bubble in self.grid.bubble_list:
            if bubble.color in COLORS:
                colors.add(bubble.color)
        # 맵에 버블이 없으면 모든 색깔 사용 가능하도록 설정함.
#         colors = set()
#         for r in range(self.grid.rows):
#             if r >= len(self.grid.map): continue # (<-- 안정성)
#             for c in range(self.grid.cols):
#                 if c >= len(self.grid.map[r]): continue # (<-- 안정성)
#                 ch = self.grid.map[r][c]
#                 if ch in COLORS:
#                     colors.add(ch)
        if not colors:
            colors = set(COLORS.keys())
        return random.choice(list(colors))

    def create_bubble(self) -> Bubble:
        color = self.random_color_from_map()
        b = Bubble(self.cannon.x, self.cannon.y, color)
        return b

    def prepare_bubbles(self) -> None:
        if self.next_bubble is not None:
            self.current_bubble = self.next_bubble
        else:
            self.current_bubble = self.create_bubble()
        self.current_bubble.x, self.current_bubble.y = self.cannon.x, self.cannon.y
        self.current_bubble.in_air = False
        self.next_bubble = self.create_bubble()

    def process_collision_and_attach(self) -> bool:
        if self.current_bubble is None:
            return False

        # --- 천장 충돌 수정 --- (<-- 수정됨)
        # grid.y_offset을 천장 기준으로 사용
        if self.current_bubble.y - self.current_bubble.radius <= (self.grid.y_offset + self.grid.wall_offset):
            r, c = self.grid.nearest_grid_to_point(self.current_bubble.x, self.current_bubble.y)
            # 천장에 붙일 땐 항상 0번째 행으로 강제
            r = 0
            self.grid.place_bubble(self.current_bubble, r, c)

            # 터지는지 확인 (<-- 추가됨)
            popped_count = self.pop_if_match(r, c)
            # 터지지 않았으면 tap 사운드 재생
            if popped_count == 0:
                if hasattr(self, 'tap_sound') and self.tap_sound:
                    try:
                        self.tap_sound.play()
                    except:
                        pass
            return True

        for b in self.grid.bubble_list:
            dist = math.hypot(self.current_bubble.x - b.x, self.current_bubble.y - b.y)
            if dist <= self.current_bubble.radius + b.radius - 2:
                r, c = self.grid.nearest_grid_to_point(self.current_bubble.x, self.current_bubble.y)
                self.grid.place_bubble(self.current_bubble, r, c)

                # 터지는지 확인 (<-- 추가됨)
                popped_count = self.pop_if_match(r, c)
                # 터지지 않았으면 tap 사운드 재생
                if popped_count == 0:
                    if hasattr(self, 'tap_sound') and self.tap_sound:
                        try:
                            self.tap_sound.play()
                        except:
                            pass
                return True

        return False

    def pop_if_match(self, row: int, col: int) -> int:
        if self.current_bubble is None:
            return 0

        if not self.grid.is_in_bounds(row, col): # (<-- 안정성)
            return 0

        color = self.grid.map[row][col]
        if color not in COLORS:
            return 0

        visited = set()
        self.grid.dfs_same_color(row, col, color, visited)

        if len(visited) >= 3:
            self.grid.remove_cells(visited)
            self.grid.remove_hanging()
            self.score_ui.add(len(visited) * 10)

            # 효과음 랜덤 재생 (<-- 추가됨)
            if hasattr(self, 'pop_sounds') and self.pop_sounds:
                random_sound = random.choice(self.pop_sounds)
                try:
                    random_sound.play()
                except:
                    pass  # 효과음 재생 실패 시 무시

            return len(visited)
        return 0

    def update(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.current_bubble and not self.fire_in_air:
                        self.fire_in_air = True
                        self.current_bubble.in_air = True
                        self.current_bubble.set_angle(self.cannon.angle)

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.cannon.rotate(+self.cannon.angle_speed)
        if keys[pygame.K_RIGHT]:
            self.cannon.rotate(-self.cannon.angle_speed)

        if self.current_bubble and self.fire_in_air:
            self.current_bubble.move()

            # --- 화면 위로 벗어난 경우 (수정) ---
            if self.current_bubble.y < -BUBBLE_RADIUS:
                self.fire_in_air = False
                self.prepare_bubbles()
                return

            if self.process_collision_and_attach():
                # process_collision_and_attach() 내부에서 이미 pop_if_match()가 호출됨
#                 rr, cc = self.current_bubble.row_idx, self.current_bubble.col_idx
#                 self.pop_if_match(rr, cc)
                self.fire_count += 1
                if self.fire_count >= LAUNCH_COOLDOWN:
                    self.grid.drop_wall()
                    self.fire_count = 0
                self.current_bubble = None
                self.fire_in_air = False
                self.prepare_bubbles()

        if self.is_stage_cleared():
            self.show_stage_clear()
            self.current_stage += 1
            # 다음 스테이지 CSV 파일이 있는지 확인
            next_csv_path = f'assets/map_data/stage{self.current_stage + 1}.csv'
            if not os.path.exists(next_csv_path):
#             if self.current_stage >= len(STAGES):
                self.running = False
                print("All stages cleared!")
            else:
                self.load_stage(self.current_stage)

        if self.lowest_bubble_bottom() > self.game_over_line:
            self.running = False
            print("Game Over")

    def is_stage_cleared(self) -> bool:
        for r in range(self.grid.rows):
            if r >= len(self.grid.map): continue # (<-- 안정성)
            for c in range(self.grid.cols):
                if c >= len(self.grid.map[r]): continue # (<-- 안정성)
                if self.grid.map[r][c] in COLORS:
                    return False
        return True

    def lowest_bubble_bottom(self) -> int:
        if not self.grid.bubble_list:
            return 0
        bottoms = [b.y + b.radius for b in self.grid.bubble_list]
        return max(bottoms)

    def draw(self) -> None:
        """화면 그리기: 모든 UI 요소 포함함."""

        # --- 1. 배경 그리기 --- (<-- 수정됨)
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            self.screen.fill((10, 20, 30)) # 대체 배경

        # --- 2. 게임 영역 배경 그리기 ---
        pygame.draw.rect(self.screen, (0, 100, 200), self.game_rect)
#         # --- 2. 파란색 게임 영역 그리기 --- (<-- 수정됨)
#         # pygame.draw.rect(self.screen, (0, 100, 200), self.game_rect) # (<-- 삭제됨)
#         if hasattr(self, 'game_area_bg'): # (<-- 추가됨)
#             self.screen.blit(self.game_area_bg, self.game_area_bg_rect) # (<-- 추가됨)
#         else: # (<-- 추가됨: 로드 실패 시 대체)
#              pygame.draw.rect(self.screen, (0, 100, 200), self.game_rect)

        # --- 3. 게임 오버 라인 그리기 (스크린샷의 녹색 선) --- (<-- 추가됨)
        pygame.draw.line(self.screen, (0, 255, 3),
                         (self.game_rect.left, self.game_over_line),
                         (self.game_rect.right, self.game_over_line), 10)

        # --- 4. 게임 오브젝트 그리기 --- (<-- 순서 변경)
        self.grid.draw(self.screen)
        self.cannon.draw(self.screen)
        if self.current_bubble:
            self.current_bubble.draw(self.screen)

        # --- 5. 캐릭터 및 로고 그리기 --- (<-- 추가됨)
        if self.char_left:
            self.screen.blit(self.char_left, (self.game_rect.left - 419, SCREEN_HEIGHT - 617))
        if self.char_right:
            self.screen.blit(self.char_right, (self.game_rect.right + 80, SCREEN_HEIGHT - 617))
        if self.logo:
            self.screen.blit(self.logo, (SCREEN_WIDTH - 198, 18 ))

        # --- 6. NEXT 버블 UI 수정 --- (<-- 수정됨)
        if self.next_bubble:
            # 다음 버블 표시 좌표 (상수로 정의되어 사용자가 쉽게 변경 가능)
            next_x = NEXT_BUBBLE_X
            next_y = SCREEN_HEIGHT + NEXT_BUBBLE_Y_OFFSET if NEXT_BUBBLE_Y_OFFSET < 0 else NEXT_BUBBLE_Y_OFFSET

            # "NEXT" 텍스트 (검은색)
            try:
                font = pygame.font.Font(ASSET_PATHS['font'], 40) if ASSET_PATHS['font'] else pygame.font.Font(None, 40)
            except:
                font = pygame.font.Font(None, 40)
            next_txt = font.render("NEXT", True, (0, 0, 0))
            next_txt_rect = next_txt.get_rect(center=(next_x, next_y - 70))
            self.screen.blit(next_txt, next_txt_rect)

            # 다음 버블을 실제 색상으로 표시
            # next_bubble의 위치를 임시로 변경하여 표시
            original_x, original_y = self.next_bubble.x, self.next_bubble.y
            self.next_bubble.x, self.next_bubble.y = next_x, next_y
            self.next_bubble.draw(self.screen)
            # 원래 위치로 복원
            self.next_bubble.x, self.next_bubble.y = original_x, original_y
#             next_x = self.cannon.x - 180 # 발사대 왼쪽
#             next_y = self.cannon.y + 80  # 발사대 살짝 아래

#             # "NEXT" 텍스트 (검은색)
#             font = pygame.font.Font(ASSET_PATHS['font'], 32)
#             next_txt = font.render("NEXT", True, (0, 0, 0))
#             next_txt_rect = next_txt.get_rect(center=(next_x, next_y - 30))
#             self.screen.blit(next_txt, next_txt_rect)

#             # 다음 버블 (흰색 원으로 표시)
#             pygame.draw.circle(self.screen, (255,255,255), (next_x, next_y + 20), self.next_bubble.radius + 2)

#             # (버블 색상 대신 흰색 원으로 표시하는 스크린샷 반영)
#             # pygame.draw.circle(
#             #     self.screen,
#             #     COLORS[self.next_bubble.color],
#             #     (next_x, next_y),
#             #     self.next_bubble.radius
#             # )
#             # pygame.draw.circle(
#             #     self.screen, (255, 255, 255), (next_x, next_y), self.next_bubble.radius, 2
#             # )


        # --- 7. 점수 UI 그리기 (레벨 전달) --- (<-- 수정됨)
        self.score_ui.draw(self.screen, self.current_stage + 1)

        # --- 8. 상단 정보 UI 제거 ---
        # (스코어/레벨이 왼쪽 상단으로 이동했으므로 기존 중앙 UI는 주석 처리)
        # font = pygame.font.Font(None, 40)
        # info = f'Stage {self.current_stage+1}/{len(STAGES)} | Shots {self.fire_count}/{LAUNCH_COOLDOWN} | Angle {int(self.cannon.angle)}'
        # ... (이하 생략) ...

        pygame.display.flip()

    def show_stage_clear(self) -> None:
        """스테이지 클리어 화면 표시"""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        font = pygame.font.Font(ASSET_PATHS['font'], 120)
        text = font.render('CLEAR!', True, (100, 255, 100))
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, rect)

        small_font = pygame.font.Font(ASSET_PATHS['font'], 50)
        info = small_font.render(
            f'Stage {self.current_stage + 1} Complete.',
            True,
            (200, 200, 200)
        )
        info_rect = info.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        self.screen.blit(info, info_rect)

        pygame.display.flip()
        pygame.time.delay(1000)

    def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)
            self.update()
            self.draw()

        # BGM 정지 (<-- 추가됨)
        pygame.mixer.music.stop()

        # 종료 화면
        self.screen.fill((0, 0, 0))
        font = pygame.font.Font(ASSET_PATHS['font'], 100)

        # 다음 스테이지 CSV 파일이 있는지 확인하여 승리/패배 판단
        next_csv_path = f'assets/map_data/stage{self.current_stage + 1}.csv'
        if not os.path.exists(next_csv_path):
#         if self.current_stage >= len(STAGES):
            msg = "YOU WIN!" # (<-- 수정됨)
        else:
            msg = "GAME OVER" # (<-- 수정됨)

        txt = font.render(msg, True, (255, 255, 255))
        rect = txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(txt, rect)

        pygame.display.flip()
        pygame.time.delay(END_SCREEN_DELAY)

def scene_factory(scene_name,manager):
    """씬 생성 팩토리"""
    if scene_name=='menu':
        return MenuScene(manager)
    # if scene_name=='game':
    #     return GameScene(manager)
    raise ValueError(f'unknown scene: {scene_name}')

def main() -> None:
    """시작점"""
    pygame.init()
    pygame.mixer.init()  # 사운드 시스템 초기화

    # FIXME: 화면 설정
    screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    clock=pygame.time.Clock()

    # MenuScene으로 일단 시작
    # manager=SceneManager(MenuScene(manager=None))
    manager=SceneManager(scene_factory)
    # manager.current_scene.manager=manager
    manager.change('menu')
        # SceneManager 연결

    running=True
    while running:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                running=False
            manager.handle_event(event)

        manager.update()
        manager.draw(screen)

        pygame.display.flip()
        # FIXME: 60FPS로 설정
        clock.tick(60)

    pygame.quit()


    if not BUBBLE_IMAGES:
        print("경고: 버블 이미지를 찾을 수 없습니다. 색상 원으로 대체합니다.")
        # (필요시, 여기서 로드 실패 시 게임을 종료할 수 있음)
        # return

    # Game().run()
    # pygame.quit()
    # sys.exit()

if __name__ == "__main__":
    main()
