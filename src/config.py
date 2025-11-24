# 화면, 게임 설정
# 기본 해상도 (원본 설계 기준)
BASE_SCREEN_WIDTH: int = 1920
BASE_SCREEN_HEIGHT: int = 1080

# 현재 화면 가로 크기 (사용자가 변경 가능) 2560/1920/1280/
# 맥북 기준 1450 적당함
# 갤럭시북 기준 1550 적당하네요.
SCREEN_WIDTH: int = 1550

SCREEN_HEIGHT: int = (SCREEN_WIDTH / 16) * 9
FPS: int = 60

# 스케일 비율 계산 (현재 해상도 / 기본 해상도)
SCALE_X: float = SCREEN_WIDTH / BASE_SCREEN_WIDTH
SCALE_Y: float = SCREEN_HEIGHT / BASE_SCREEN_HEIGHT
SCALE: float = min(SCALE_X, SCALE_Y)  # 비율 유지를 위해 작은 값 사용

# 게임 플레이 설정 (기본값, 스케일 적용됨)
BASE_CELL_SIZE: int = 100
BASE_BUBBLE_RADIUS: int = 47
BASE_BUBBLE_SPEED: int = 30

# 스케일 적용된 값
CELL_SIZE: int = int(BASE_CELL_SIZE * SCALE)
BUBBLE_RADIUS: int = int(BASE_BUBBLE_RADIUS * SCALE)
BUBBLE_SPEED: int = int(BASE_BUBBLE_SPEED * SCALE)

LAUNCH_COOLDOWN: int = 4
WALL_DROP_PIXELS: int = CELL_SIZE

# 맵 설정
MAP_ROWS: int = 6
MAP_COLS: int = 8

# 다음 버블 미리보기 표시 좌표 (사용자가 임의로 설정 가능)
NEXT_BUBBLE_X = 750
    # 다음 버블 표시 x좌표
NEXT_BUBBLE_Y_OFFSET = -80
    # 다음 버블 표시될 위치를 조정하는 수치
        # 음수면 아래에서 위로
