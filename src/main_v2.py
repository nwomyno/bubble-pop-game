import math
import random
import sys
from typing import List, Set, Tuple, Optional
import pygame

# --- 에셋 파일 경로 ---  (<-- 추가됨)
# 사용자의 실제 파일 경로로 수정하세요.
ASSET_PATHS = {
    'bubble_red': 'assets/bubble_red.png',
    'bubble_yellow': 'assets/bubble_yellow.png',
    'bubble_blue': 'assets/bubble_blue.png',
    'bubble_green': 'assets/bubble_green.png',
    'background': 'assets/background.png',
    'game_area_bg': 'assets/bg_box.png', # (<-- 추가됨)
    'char_left': 'assets/char_left.png',
    'char_right': 'assets/char_right.png',
    'logo': 'assets/logo.png',
    'cannon_arrow': 'assets/cannon_arrow.png', # 십자+화살표 이미지
    'font': None  # None으로 설정 시 기본 폰트 사용, 'assets/pixel_font.ttf' 등으로 변경 가능
}

# 게임 초기화
pygame.init()

# 버블 이미지 로드 (45x45 → 48x48로 확대)
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
SCREEN_WIDTH: int = 1920
SCREEN_HEIGHT: int = 1080
FPS: int = 60

UI_ALPHA = 180
END_SCREEN_DELAY = 300

CELL_SIZE: int = 98
BUBBLE_RADIUS: int = 37
BUBBLE_SPEED: int = 14

# ======== 이미지 크기 조정 ========
if BUBBLE_IMAGES:
    target_size = BUBBLE_RADIUS * 2
    for color in BUBBLE_IMAGES:
        BUBBLE_IMAGES[color] = pygame.transform.smoothscale(
            BUBBLE_IMAGES[color],
            (target_size, target_size)
        )
    print(f"버블 이미지 크기 조정 완료: {target_size}x{target_size}px")

LAUNCH_COOLDOWN: int = 4
WALL_DROP_PIXELS: int = CELL_SIZE

COLORS: dict[str, Tuple[int, int, int]] = {
    'R': (220, 50, 50),
    'Y': (240, 200, 60),
    'B': (60, 100, 240),
    'G': (70, 200, 120),
}

# 맵 크기 (<-- 수정됨: 스크린샷에 맞게 12x10으로 변경)
MAP_ROWS: int = 6
MAP_COLS: int = 8

# 맵 데이터 (<-- 수정됨: 12열에 맞게 스테이지 데이터 축소)
STAGES: List[List[List[str]]] = [
    # 스테이지 1
    [
        list("RRYYGGBBRRYY"),
        list("RRYYGGBBRRYG"), # / 대신 G로 채움
        list("BBGGRRYYBBGG"),
        list("BBGGRRYYBBGR"), # / 대신 R로 채움
        list("............"),
        list("............"),
        list("............"),
        list("............"),
        list("............"),
        list("............"),
    ],
    # 스테이지 2
    [
        list("R.Y.G.B.R.Y."),
        list("Y.G.B.R.Y.G."),
        list("G.B.R.Y.G.B."),
        list("B.R.Y.G.B.R."),
        list("....RRGGYYBB"),
        list("....RRGGYYBB"),
        list("............"),
        list("............"),
        list("............"),
        list("............"),
    ],
]

# ======== 유틸리티 함수 정의 ========
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

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
        self.angle_speed: float = 2.0

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
    def __init__(self, rows: int, cols: int, cell_size: int, wall_offset: int = 0, x_offset: int = 0, y_offset: int = 0) -> None:
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
        # 맵의 실제 너비를 계산
        map_pixel_width = (MAP_COLS * CELL_SIZE) + (CELL_SIZE // 2) 
        self.grid_x_offset = (SCREEN_WIDTH - map_pixel_width) // 2
        self.grid_y_offset = 100 # 상단 여백

        # 파란색 게임 영역 사각형 정의
        padding = 20
        game_area_w = map_pixel_width + (padding * 2)
        game_area_h = SCREEN_HEIGHT - self.grid_y_offset - 50 # 하단 여백 50
        game_area_x = (SCREEN_WIDTH - game_area_w) // 2
        game_area_y = self.grid_y_offset - padding
        self.game_rect = pygame.Rect(game_area_x, game_area_y, game_area_w, game_area_h)

        # --- HexGrid 초기화 수정 --- (<-- 수정됨)
        self.grid: HexGrid = HexGrid(MAP_ROWS, MAP_COLS, CELL_SIZE, 0, self.grid_x_offset, self.grid_y_offset)

        # --- 발사대 위치 수정 --- (<-- 수정됨)
        cannon_x = self.game_rect.centerx
        cannon_y = self.game_rect.bottom - 120  # 게임 영역 하단에서 60px 위
        self.cannon: Cannon = Cannon(cannon_x, cannon_y)

        # --- 게임 오버 라인 수정 --- (<-- 수정됨)
        self.game_over_line = self.cannon.y - CELL_SIZE * 0.5

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
            
            # (<-- 추가됨) 게임 영역 배경 이미지 로드
            self.game_area_bg = pygame.image.load(ASSET_PATHS['game_area_bg']).convert_alpha()
            # 원본 크기 사용, 앵커(중심)만 self.game_rect의 중심으로 설정
            self.game_area_bg_rect = self.game_area_bg.get_rect(center=self.game_rect.center)
            
        except pygame.error as e:
            print(f"배경/UI 이미지 로드 실패: {e}")
            self.background_image = None
            self.char_left = None
            self.char_right = None
            self.logo = None


        # 게임 상태
        self.current_stage: int = 0
        self.current_bubble: Optional[Bubble] = None
        self.next_bubble: Optional[Bubble] = None
        self.fire_in_air: bool = False
        self.fire_count: int = 0
        self.running: bool = True

        self.load_stage(self.current_stage)

    def load_stage(self, stage_index: int) -> None:
        if stage_index >= len(STAGES):
            self.running = False # 모든 스테이지 클리어
            return
            
        stage_map = STAGES[stage_index]
        
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
        colors = set()
        for r in range(self.grid.rows):
            if r >= len(self.grid.map): continue # (<-- 안정성)
            for c in range(self.grid.cols):
                if c >= len(self.grid.map[r]): continue # (<-- 안정성)
                ch = self.grid.map[r][c]
                if ch in COLORS:
                    colors.add(ch)
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
            return True

        for b in self.grid.bubble_list:
            dist = math.hypot(self.current_bubble.x - b.x, self.current_bubble.y - b.y)
            if dist <= self.current_bubble.radius + b.radius - 2:
                r, c = self.grid.nearest_grid_to_point(self.current_bubble.x, self.current_bubble.y)
                self.grid.place_bubble(self.current_bubble, r, c)
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
                rr, cc = self.current_bubble.row_idx, self.current_bubble.col_idx
                self.pop_if_match(rr, cc)
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
            if self.current_stage >= len(STAGES):
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

        # --- 2. 파란색 게임 영역 그리기 --- (<-- 수정됨)
        # pygame.draw.rect(self.screen, (0, 100, 200), self.game_rect) # (<-- 삭제됨)
        if hasattr(self, 'game_area_bg'): # (<-- 추가됨)
            self.screen.blit(self.game_area_bg, self.game_area_bg_rect) # (<-- 추가됨)
        else: # (<-- 추가됨: 로드 실패 시 대체)
             pygame.draw.rect(self.screen, (0, 100, 200), self.game_rect)

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
            next_x = self.cannon.x - 180 # 발사대 왼쪽
            next_y = self.cannon.y + 80  # 발사대 살짝 아래
            
            # "NEXT" 텍스트 (검은색)
            font = pygame.font.Font(ASSET_PATHS['font'], 32)
            next_txt = font.render("NEXT", True, (0, 0, 0))
            next_txt_rect = next_txt.get_rect(center=(next_x, next_y - 30))
            self.screen.blit(next_txt, next_txt_rect)

            # 다음 버블 (흰색 원으로 표시)
            pygame.draw.circle(self.screen, (255,255,255), (next_x, next_y + 20), self.next_bubble.radius + 2)
            
            # (버블 색상 대신 흰색 원으로 표시하는 스크린샷 반영)
            # pygame.draw.circle(
            #     self.screen,
            #     COLORS[self.next_bubble.color],
            #     (next_x, next_y),
            #     self.next_bubble.radius
            # )
            # pygame.draw.circle(
            #     self.screen, (255, 255, 255), (next_x, next_y), self.next_bubble.radius, 2
            # )


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

        # 종료 화면
        self.screen.fill((0, 0, 0))
        font = pygame.font.Font(ASSET_PATHS['font'], 100)
        
        if self.current_stage >= len(STAGES):
            msg = "YOU WIN!" # (<-- 수정됨)
        else:
            msg = "GAME OVER" # (<-- 수정됨)

        txt = font.render(msg, True, (255, 255, 255))
        rect = txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(txt, rect)

        pygame.display.flip()
        pygame.time.delay(END_SCREEN_DELAY)

def main() -> None:
    # 프로그램 시작점
    if not BUBBLE_IMAGES:
        print("경고: 버블 이미지를 찾을 수 없습니다. 색상 원으로 대체합니다.")
        # (필요시, 여기서 로드 실패 시 게임을 종료할 수 있음)
        # return 
        
    Game().run()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()