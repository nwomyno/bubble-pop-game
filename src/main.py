# Bubble Pop MVP -
import math
    # 발사 각도 계산, 충돌 거리 측정, 라디안 변환 목적
import random
    # 발사할 버블 색깔 랜덤 선택 목적
import sys
    # 프로그램 완전 종료; 리소스 안전 해제 목적
import pygame
    # 게임 엔진

# 게임 초기화함.
pygame.init()

# ======== 전역 설정 ========
# 화면 설정
""" 테스트용: 나중에 각각 1920, 1080으로 수정 """
SCREEN_WIDTH=1080
    # 화면 너비
SCREEN_HEIGHT=640
    # 화면 높이
FPS=60

# 게임 오브젝트 크기 설정
CELL_SIZE=64
    # 육각형 격자 셀 간격
BUBBLE_RADIUS=24
    # 버블 반지름
BUBBLE_SPEED=14
    # 버블 발사 속도

# 발사 후 떨어지는 버블 수: 4발
# 게임 규칙
LAUNCH_COOLDOWN=4
    # 4발 쏘면 벽 한 칸 하강함.
WALL_DROP_PIXELS=CELL_SIZE
    # 벽 하강 픽셀 수

# 버블 색상 정의 (네 가지)
COLORS={
    'R':(220,50,50),
        # 빨강
    'Y':(240,200,60),
        # 노랑
    'B':(60,100,240),
        # 파랑
    'G':(70,200,120),
        # 초록
}

# 맵 크기
MAP_ROWS=12
    # 격자 행 수
MAP_COLS=16
    # 격자 열 수

# 맵 데이터 1개만
""" R, Y, G, ...: 각 색상의 앞글자를 가리킴. """
STAGES=[
    # 스테이지 1: 초급 난이도
    [
        list("RRYYGGBBRRYYGG.."),
        list("RRYYGGBBRRYYG/.."),
        list("BBGGRRYYBBGGRR.."),
        list("BGGRRYYBBGGRR/.."),
        list("................"),
        list(".............../"),
        list("................"),
        list(".............../"),
        list("................"),
        list(".............../"),
        list("................"),
        list("................"),
    ],
    # 스테이지 2: 중급 난이도
    [
        list("..R..Y..B..G..RR"),
        list("..G..B..R..Y./YY"),
        list("R.R.R.R.R.R.R.R."),
        list("Y.Y.Y.Y.Y.Y.Y./."),
        list("................"),
        list(".............../"),
        list("....RRGGYYBB...."),
        list("....RRGGYYBB../."),
        list("................"),
        list(".............../"),
        list("................"),
        list("................"),
    ],
    # 스테이지 3: 고급 난이도
    [
        list("RGBYRGBYRGBYRGBY"),
        list("RGBYRGBYRGBYRG/"),
        list("................"),
        list(".............../"),
        list("GGGG........RRRR"),
        list("GGGG......./RRRR"),
        list("................"),
        list(".............../"),
        list("BBBB........YYYY"),
        list("BBBB......./YYYY"),
        list("................"),
        list("................"),
    ],
]

# ======== 유틸리티 함수 정의 ========
def clamp(v, lo, hi):
    # PARAMETERS: value, min_value, max_value
    return max(lo,min(hi,v))
    """ 값을 범위 내로 제한함. """

# ======== 버블 클래스 - 버블 객체 ========
class Bubble:
    """ 게임의 각 버블을 표현함. 버블의 위치, 색깔, 상태를 관리하고 화면에 그림. """
    def __init__(self,x,y,color,radius=BUBBLE_RADIUS):
        self.x=x
            # 버블 x좌표
        self.y=y
            # 버블 y좌표
        self.color=color
            # 버블 색깔, 예를 들어: R, Y, B, G
        self.radius=radius
            # 버블 반지름
        self.in_air=False
            # 발사 중인지 여부 체크
        self.is_attached=False
            # 격자에 부착됐는지 여부 체크
        self.angle_degree=90
            # 발사 각도
        self.speed=BUBBLE_SPEED
            # 이동 속도
        self.row_idx=-1
            # 격자 행 인덱스: 격자에 배치되지 않은 상태로 초기화(-1)
        self.col_idx=-1
            # 격자 행 인덱스: 격자에 배치되지 않은 상태로 초기화(-1)

    # 버블을 화면에 그림.
    def draw(self,screen):
        # TODO: 색깔 딕셔너리를 써서 버블 원 그리기.
        # TODO: 테두리 추가해서 가독성 향상시키기.
        # 버블 원 그림.
        pygame.draw.circle(screen,COLORS[self.color],(int(self.x),int(self.y)),self.radius)
        # 흰색 테두리 추가해서 가독성 향상시킴.
        pygame.draw.circle(screen,(255,255,255),(int(self.x),int(self.y)),self.radius,2)

    # 발사 각도 설정함.
    def set_angle(self,angle_degree):
        # TODO: 발사 각도 저장하기.
        self.angle_degree=angle_degree

    # 격자 인덱스 설정함.
    def set_grid_index(self,r,c):
        # PARAMETERS: *r: row, *c: column
        # TODO: 행, 열 인덱스 저장하기.
        self.row_idx=r
        self.col_idx=c

    # 벽 반사 포함해서 발사된 버블 이동.
    def move(self):
        """ 왼쪽, 오른쪽 벽 반사하는 로직,
        입사각이랑 반사각이랑 같게끔 만드는 로직 사용. """
        # TODO: 각도를 라디안으로 변환하기.
        # TODO: cos, sin으로 이동 벡터 계산하기.
        # TODO: 좌우 벽 반사 처리하기. (각도 반전)
        rad=math.radians(self.angle_degree)
        # 각도에 따라서 x,y 이동시키는 로직
        dx=self.speed*math.cos(rad)
        dy=-self.speed*math.sin(rad)
        self.x+=dx
        self.y+=dy

        # 왼쪽 벽에 충돌하는 경우.
        if self.x-self.radius<0:
            self.x=self.radius
                # 위치 보정: 벽 안쪽으로 되돌리는 로직
            self.angle_degree=180-self.angle_degree
                # 입사각, 반사각 같게 만들기 위해 반사각 계산하는 로직
        # 오른쪽 벽에 충돌하는 경우.
        elif self.x+self.radius>SCREEN_WIDTH:
            self.x=SCREEN_WIDTH-self.radius
            self.angle_degree=180-self.angle_degree

# ======== Cannon 클래스: 발사대 ========
class Cannon:
    """ 버블을 발사하는 발사대 정의. 각도 조정, 조준선을 화면에 그리는 역할. """
    def __init__(self,x,y):
        self.x=x
            # 발사대 x 좌표
        self.y=y
            # 발사대 y 좌표
        self.angle=90
            # 발사 각도 (default: 위쪽)
        self.min_angle=10
            # 최소 각도 제한
        self.max_angle=170
            # 최대 각도 제한
        self.angle_speed=2.0
            # 회전 속도

    # 키보드 입력으로 각도 조정함.
    def rotate(self,delta):
        # TODO: 각도 증감하고 나서 범위 제한하기 (clamp 사용해서)
        self.angle+=delta
        self.angle=clamp(self.angle,self.min_angle,self.max_angle)
            # 각도 범위 제한

    # 발사대 조준선 그리는 역할.
    def draw(self,screen):
        # TODO: 각도 이용해서 조준선 끝점 계산하기.
        # TODO: 선, 중심점 그리기.
        length=100
        rad=math.radians(self.angle)
            # 각도를 라디안으로 변환.
        # 발사대 끝 좌표 계산하는 로직
        end_x=self.x+length*math.cos(rad)
        end_y=self.y-length*math.sin(rad)
        pygame.draw.line(screen,(255,255,255),(self.x,self.y),(end_x,end_y),4)
            # 흰색 조준선 그림.
        pygame.draw.circle(screen,(255,0,0),(self.x,self.y),6)
            # 빨간색 중심점 그림.


# ======== HexGrid 클래스 - 육각형 격자 체계 ========
class HexGrid:
    """ 육각형 모양 배열의 버블 격자를 관리함. 버블 배치, 충돌, 터뜨리기, 자유낙하 등의 로직을 처리함. """
    def __init__(self,rows,cols,cell_size,wall_offset=0):
        self.rows=rows
            # 격자 행 수
        self.cols=cols
            # 격자 열 수
        self.cell=cell_size
            # 셀 크기
        self.wall_offset=wall_offset
            # 벽 하강 오프셋
        self.map=[['.' for _ in range(cols)] for _ in range(rows)]
            # '.'으로 채워진 2차원 배열 생성
        self.bubble_list=[]
            # 화면에 있는 버블 리스트

    # 스테이지 맵 로드함.
    def load_from_stage(self,stage_map):
        # TODO: 맵 데이터를 읽어서 버블 만들기.
        # TODO: 각 버블에 격자 인덱스 할당하기.
        self.map=[row[:] for row in stage_map]
            # 원본 STAGES 데이터를 보호하기 위해 각 행 복사 후 2차원 리스트를 새로 만드는 로직
        self.bubble_list=[]
            # 기존 버블 객체 모두 제거함.

        for r in range(self.rows):
            for c in range(self.cols):
                ch=self.map[r][c] if c < len(self.map[r]) else '.'
                    # 열 인덱스가 현재 행의 길이보다 작은지 확인함.
                        # True이면 해당 위치 문자 반환
                # 딕셔너리 안에 키가 존재하는지 확인.
                if ch in COLORS:
                    x,y=self.get_cell_center(r,c)
                    b=Bubble(x,y,ch)
                    b.is_attached=True
                    b.set_grid_index(r,c)
                    self.bubble_list.append(b)


    # 육각 격자의 중심 좌표를 계산함.
    def get_cell_center(self,r,c):
        # PARAMETERS: *r: row, *c: column
        # TODO: 짝수, 홀수 행에 따라서 다른 오프셋을 적용하기.
        # TODO: x, y 좌표 반환하기.
        """ 육각형 배열은 지그재그 배열을 사용하기 때문에 이런 계산 로직을 사용함; 육각 격자 체계의 핵심 로직 """
        x=c*self.cell+self.cell//2
        y=r*self.cell+self.cell//2+self.wall_offset
        # 홀수 행은 오른쪽으로 반 칸 이동.
        if r%2==1:
            x+=self.cell//2
        return x,y


    # 화면 좌표를 격자 인덱스로 바꿈.
    def screen_to_grid(self,x,y):
        # TODO: 픽셀 좌표를 행, 열 인덱스로 변환하기.
        r=int((y-self.wall_offset)//self.cell)
        # r값이 음수 안되게 전처리
        if r<0:
            r=0
        c=int(x//self.cell)

        # 홀수 행은 육각형 배열이라 오른쪽으로 반칸 이동해있기 때문에 오프셋 보정하는 로직임.
        if r%2==1:
            c=int((x-self.cell//2)//self.cell)
        c=clamp(c,0,self.cols-1)
        r=clamp(r,0,self.rows-1)
        return r,c


    # 버블을 격자에 배치함.
    def place_bubble(self,bubble,r,c):
        # TODO: 맵에 색깔 기록하기.
        # TODO: 버블 위치 조정하고 리스트에 추가하기.
        if self.map[r][c]=='/':
            c=clamp(c+1,0,self.cols-1)

        self.map[r][c]=bubble.color
        cx,cy=self.get_cell_center(r,c)
        bubble.x,bubble.y=cx,cy
        bubble.is_attached=True
        bubble.in_air=False
        bubble.set_grid_index(r,c)
        self.bubble_list.append(bubble)

    # 충돌 지점 근처의 빈 격자를 찾음.
    def nearest_grid_to_point(self,x,y):
        # TODO: 충돌 지점의 격자 인덱스를 계산함.
        # TODO: 이웃 중 빈 칸을 찾음.
        r,c=self.screen_to_grid(x,y)
            # input받은 좌표에서 가장 가까운 빈 격자 찾음.

        # 이 위치에 이미 버블이 있거나 슬래시 문자가 있는 경우
        if self.map[r][c] in COLORS or self.map[r][c]=='/':
            neighbors=self.get_neighbors(r,c)
            # 각 neighbor 순회하면서 빈칸 찾으면 바로 반환.
            for nr,nc in neighbors:
                if self.is_in_bounds(nr,nc) and self.map[nr][nc]=='.':
                    return nr, nc
        return r,c

    # 격자 범위를 체크함.
    def is_in_bounds(self,r,c):
        # TODO: 행, 열이 맵 범위 내에 있는지 확인하기.
        return 0<=r<self.rows and 0<=c<self.cols

    # 육각 격자의 6개 이웃 좌표를 반환함.
    def get_neighbors(self,r,c):
        # TODO: 짝수, 홀수 행에 따라서 다른 이웃 배열 반환하기.
        # 짝수 행이면
        if r%2==0:
            dr=[0,-1,-1,0,1,1]
                # 델타 row
            dc=[-1,-1,0,1,0,-1]
                # 델타 column
        # 홀수 행이면
        else:
            dr=[0,-1,-1,0,1,1]
            dc=[-1,0,1,1,1,0]
        return [(r+dr[i],c+dc[i]) for i in range(6)]


    # 같은 색깔 버블을 DFS 탐색함.
    def dfs_same_color(self,row,col,color,visited):
        # TODO: 재귀적으로 같은 색깔 버블 찾기.
        # TODO: `visited` 집합에 좌표 추가하기.
        pass

    # 특정 셀 제거함.
    def remove_cells(self,cells):
        # TODO: 맵에서 제거하기. ('.' 처리)
        # TODO: bubble_list에서 제거하기.
        pass

    # 천장과 연결된 버블을 찾음. (DFS)
    def flood_from_top(self):
        # TODO: 첫 번째 행에서 DFS 시작하기.
        # TODO: 연결된 버블 집합 반환하기.
        pass

    # 천장 연결 DFS를 수행함.
    def _dfs_reachable(self,row,col,visited):
        # TODO: 재귀적으로 천장과 연결된 버블 탐색하기.
        pass

    # 천장과 연결되지 않은 버블을 제거함. (자유낙하)
    def remove_hanging(self):
        # TODO: 천장 연결 버블 찾기.
        # TODO: 연결되지 않은 버블 삭제하기.
        pass

    # 모든 버블을 그림.
    def draw(self,screen):
        # TODO: bubble_list에 들어있는 모든 버블 draw() 호출하기.
        for b in self.bubble_list:
            b.draw(screen)

    # 벽 하강시킴. (4발 발사한 뒤)
    def drop_wall(self):
        # TODO: wall_offset 증가시키기.
        # TODO: 모든 버블 위치 재계산하기.
        pass

# ======== ScoreDisplay 클래스 - 점수 표시 ========
class ScoreDisplay:
    """ 게임의 현재 점수를 표시하는 UI. """
    def __init__(self):
        self.score=0
            # 초기 점수
        self.font=pygame.font.Font(None,40)
            # 폰트

    # 점수 추가함.
    def add(self,points):
        # TODO: 점수 증가시키기.
        pass

    # 점수를 화면에 표시함.
    def draw(self,screen):
        # TODO: 점수 텍스트 렌더링하고 화면 출력하기.
        pass

# ======== Game 클래스 - 메인 게임 로직 ========
class Game:
    """ 게임의 전체 로직을 관리하는 메인 클래스임. 초기화, 업데이트, 그리기, 이벤트 처리를 담당함. """
    def __init__(self):
        # 화면 설정
        self.screen=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
        pygame.display.set_caption("Bubble Pop MVP")
            # 게임 창의 제목 표시줄에 표시될 텍스트 설정
        self.clock=pygame.time.Clock()
            # 게임 프레임 속도 제어하는 로직 (Clock 객체 생성)
        self.grid=HexGrid(MAP_ROWS,MAP_COLS,CELL_SIZE,wall_offset=0)
        self.running=True

        # 게임 오브젝트 초기화
        self.cannon=Cannon(SCREEN_WIDTH//2,SCREEN_HEIGHT-120)
            # 화면 하단 중간에 배치해놓기.
        self.score_ui=ScoreDisplay()

        # 게임 상태
        self.current_stage=0
            # 현재 스테이지 인덱스
        self.current_bubble=None
            # 현재 발사할 버블
        self.next_bubble=None
            # 다음 버블 (미리보기)
        self.fire_in_air=False
            # 발사 중인지 여부
        self.fire_count=0
            # 발사 횟수 (4발마다 벽 하강함)
        self.running=True
            # 게임 실행 여부
        self.prepare_bubbles()
            # 처음 버블 준비

        # 스테이지 로드 (임시)
        # self.load_stage(self.current_stage)
        # 첫 번째 스테이지 로드
        self.grid.load_from_stage(STAGES[self.current_stage])

    # 스테이지 로드함.
    def load_stage(self,stage_index):
        # TODO: STAGES에서 맵 데이터 가져오기.
        # TODO: grid.load_from_stage() 호출하기.
        # TODO: 초기 버블 준비하기.
        pass

    # 맵에 존재하는 색깔 중 랜덤 선택함.
    def random_color_from_map(self):
        # TODO: 맵을 순회하면서 존재하는 색깔 수집하기.
        # TODO: random.choice()로 선택하기.
        colors=set()
            # 빈 집합 생성
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                ch=self.grid.map[r][c]
                    # 색상 추출
                if ch in COLORS:
                    colors.add(ch)
        # 맵에 버블이 없으면 모든 색깔 사용 가능하도록 설정함.
        if not colors:
            colors=set(COLORS.keys())
        return random.choice(list(colors))


    # 새 버블 생성함.
    def create_bubble(self):
        # TODO: random_color_from_map()로 색깔 선택하기.
        # TODO: Bubble 인스턴스 생성하기.
        color=self.random_color_from_map()
        b=Bubble(self.cannon.x,self.cannon.y,color)
        return b

    # 현재, 다음 버블 준비함.
    def prepare_bubbles(self):
        # TODO: next_bubble을 current_bubble로 이동시키기.
        # TODO: 새로운 next_bubble 생성하기.
        if self.next_bubble is not None:
            self.current_bubble=self.next_bubble
                # 다음 버블을 현재 버블로 이동함.
        else:
            self.current_bubble=self.create_bubble()
        self.current_bubble.x,self.current_bubble.y=self.cannon.x,self.cannon.y

        self.current_bubble.in_air=False

        self.next_bubble=self.create_bubble()



    # 충돌, 부착 처리함.
    def process_collision_and_attach(self):
        # TODO: 천장 충돌 체크하기.
        # TODO: 기존 버블과 충돌 체크하기. (거리 계산)
        # TODO: 충돌 시 place_bubble() 호출하기.
        # 천장 충돌 로직:
        if self.current_bubble.y-self.current_bubble.radius<=self.grid.wall_offset:
            r,c=self.grid.nearest_grid_to_point(self.current_bubble.x,self.current_bubble.y)
            self.grid.place_bubble(self.current_bubble,r,c)
            return True

        # 기존 버블과 충돌하게끔 함. (거리도 hypot으로 계산)
        for b in self.grid.bubble_list:
            dist=math.hypot(self.current_bubble.x-b.x,self.current_bubble.y-b.y)

            # 겹치는 걸 방지하기 위해서 충돌을 더 일찍 감지하게끔.
                # 여유 있게 값 2로 세팅.
            if dist<=self.current_bubble.radius+b.radius-2:
                r,c=self.grid.nearest_grid_to_point(self.current_bubble.x,self.current_bubble.y)

                self.grid.place_bubble(self.current_bubble,r,c)
                return True

        return False

    # 3개 이상 연결 시 터뜨림.
    def pop_if_match(self,row,col):
        # TODO: DFS로 같은 색깔 버블 찾기.
        # TODO: 3개 이상이면 제거하고 점수 추가하기.
        # TODO: 자유낙하 버블 제거하기.
        pass

    # 게임 로직 업데이트함.
    def update(self):
        # TODO: 이벤트 처리하기. (키보드 입력)
        # TODO: 발사체 이동, 충돌 처리하기.
        # TODO: 4발마다 벽 하강시키기.
        # TODO: 스테이지 클리어, 게임 오버 체크하기.
        # 이벤트 큐에 쌓인 모든 이벤트를 가져옴.
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                self.running=False

            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_LEFT:
                    self.cannon.rotate(+self.cannon.angle_speed)
                        # 왼쪽 키 입력하면 반시계 방향으로 rotate
                elif event.key==pygame.K_RIGHT:
                    self.cannon.rotate(-self.cannon.angle_speed)
                        # 오른쪽 키 입력하면 시계 방향으로 rotate
                elif event.key==pygame.K_SPACE:
                    if self.current_bubble and not self.fire_in_air:
                        self.fire_in_air=True
                        self.current_bubble.in_air=True
                        self.current_bubble.set_angle(self.cannon.angle)

        if self.current_bubble and self.fire_in_air:
            self.current_bubble.move()
                # 발사체 이동함.
            if self.process_collision_and_attach():
                self.fire_in_air=False
                self.prepare_bubbles()

    # 스테이지 클리어 여부 확인함.
    def is_stage_cleared(self):
        # TODO: 맵에 버블이 남아있는지 체크하기.
        pass

    # 가장 아래 버블의 y좌표 구함.
    def lowest_bubble_bottom(self):
        # TODO: bubble_list에서 최대 y 값 찾기.
        pass

    # 화면 그림.
    def draw(self):
        # TODO: 배경 색깔 채우기.
        # TODO: 격자, 발사대, 버블 그리기.
        # TODO: UI (점수, 다음 버블, 정보) 표시하기.
        self.screen.fill((10,20,30))
            # RGB 색상으로 채우기: 일단 임시로 어두운 파란색 배경
        self.grid.draw(self.screen)
            # 격자 버블 그림.
        self.cannon.draw(self.screen)
            # cannon도 그림.

        if self.current_bubble:
            self.current_bubble.draw(self.screen)
                # 현재 버블이면 현재 버블 그리기.

        pygame.display.flip()
            # 디스플레이 갱신함.

    # 메인 게임 루프 실행함.
    def run(self):
        while self.running:
            self.clock.tick(FPS)
                # 프레임 속도 제한함.
            self.update()
            # for event in pygame.event.get():
            #     if event.type==pygame.QUIT:
            #         self.running=False
            self.draw()

        # 종료 화면
        # TODO: 승리, 패배 메시지 표시하기.
        pass

def main():
    Game().run()
    pygame.quit()
    sys.exit()

if __name__=="__main__":
    main()
