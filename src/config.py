# 화면, 게임 설정
SCREEN_WIDTH: int = 1920
SCREEN_HEIGHT: int = 1080
FPS: int = 60

# 게임 플레이 설정
CELL_SIZE: int = 100
BUBBLE_RADIUS: int = 47
BUBBLE_SPEED: int = 30

LAUNCH_COOLDOWN: int = 4
WALL_DROP_PIXELS: int = CELL_SIZE

# 맵 설정
MAP_ROWS: int = 6
MAP_COLS: int = 8

# FIXME: 하드코딩된 값보다 유연하게 배치해놓음.
# 다음 버블 미리보기 표시 좌표 (사용자가 임의로 설정 가능)
NEXT_BUBBLE_X = 750
# NEXT_BUBBLE_X = SCREEN_WIDTH//2
    # 화면 [수정]
    # 다음 버블 표시 x좌표
NEXT_BUBBLE_Y_OFFSET = -80
# NEXT_BUBBLE_Y_OFFSET = -50
    # 오프셋 조정 [수정]
    # 다음 버블 표시될 위치를 조정하는 수치
        # 음수면 아래에서 위로
