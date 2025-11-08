# Bubble Pop MVP
import math
    # 발사 각도 계산, 충돌 거리 측정, 라디안 변환 목적
import random
    # 발사할 버블 색깔 랜덤 선택 목적
import sys
    # 프로그램 완전 종료; 리소스 안전 해제 목적
from typing import List,Set,Tuple,Optional
    # 타입 힌트용 임포트
import pygame
    # 게임 엔진

# 게임 초기화함.
pygame.init()

# ======== 전역 설정 ========
# 화면 설정
""" 테스트용: 나중에 각각 1920, 1080으로 수정 """
SCREEN_WIDTH:int=1440
    # 화면 너비
SCREEN_HEIGHT:int=720
    # 화면 높이
FPS:int=60
    # 초당 프레임 수

# 투명도 값
UI_ALPHA=180

# 종료 화면 딜레이 값 (ms)
END_SCREEN_DELAY=300

# 게임 오브젝트 크기 설정
CELL_SIZE:int=64
    # 육각형 격자 셀 간격
BUBBLE_RADIUS:int=24
    # 버블 반지름
BUBBLE_SPEED:int=14
    # 버블 발사 속도

# 발사 후 떨어지는 버블 수: 4발
# 게임 규칙
LAUNCH_COOLDOWN:int=4
    # 4발 쏘면 벽 한 칸 하강함.
WALL_DROP_PIXELS:int=CELL_SIZE
    # 벽 하강 픽셀 수

# 버블 색상 정의 (네 가지)
COLORS:dict[str,Tuple[int,int,int]]={
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
MAP_ROWS:int=12
    # 격자 행 수
MAP_COLS:int=22
    # 격자 열 수

# 맵 데이터 1개만
""" R, Y, G, ...: 각 색상의 앞글자를 가리킴. """
STAGES: List[List[List[str]]] = [
    # 스테이지 1: 초급 난이도 - 기본 클러스터
    [
        list("RRYYGGBBRRYYGGBBRRYYGGBB"),
        list("RRYYGGBBRRYYGGBBRRYYGG/B"),
        list("BBGGRRYYBBGGRRYYBBGGRRYY"),
        list("BBGGRRYYBBGGRRYYBBGGRR/Y"),
        list("........................"),
        list("........................"),
        list("........................"),
        list("........................"),
        list("........................"),
        list("........................"),
        list("........................"),
        list("........................"),
    ],

    # 스테이지 2: 중급 난이도 - 산발적 배치
    [
        list("R.Y.G.B.R.Y.G.B.R.Y.G.B."),
        list("Y.G.B.R.Y.G.B.R.Y.G.B./R"),
        list("G.B.R.Y.G.B.R.Y.G.B.R.Y."),
        list("B.R.Y.G.B.R.Y.G.B.R.Y./G"),
        list("........................"),
        list("........................"),
        list("....RRRRGGGGYYYYBBBB...."),
        list("....RRRRGGGGYYYYBBB/...."),
        list("........................"),
        list("........................"),
        list("........................"),
        list("........................"),
    ],

    # 스테이지 3: 고급 난이도 - 대칭 패턴
    [
        list("RGBYRGBYRGBYRGBYRGBYRGBY"),
        list("RGBYRGBYRGBYRGBYRGBYRG/Y"),
        list("........................"),
        list("........................"),
        list("GGGGGGGG........RRRRRRRR"),
        list("GGGGGGGG......./RRRRRRRR"),
        list("........................"),
        list("........................"),
        list("BBBBBBBB........YYYYYYYY"),
        list("BBBBBBBB......./YYYYYYYY"),
        list("........................"),
        list("........................"),
    ],
]
# ======== 유틸리티 함수 정의 ========
def clamp(v:float,lo:float,hi:float)->float:
    # PARAMETERS: value, min_value, max_value
    return max(lo,min(hi,v))
    """ 값을 범위 내로 제한함. """

# ======== 버블 클래스 - 버블 객체 ========
class Bubble:
    """ 게임의 각 버블을 표현함. 버블의 위치, 색깔, 상태를 관리하고 화면에 그림. """
    def __init__(self,x:float,y:float,color:str,radius:int=BUBBLE_RADIUS)->None:
        self.x:float=x
            # 버블 x좌표
        self.y:float=y
            # 버블 y좌표
        self.color:str=color
            # 버블 색깔, 예를 들어: R, Y, B, G
        self.radius:int=radius
            # 버블 반지름
        self.in_air:bool=False
            # 발사 중인지 여부 체크
        self.is_attached:bool=False
            # 격자에 부착됐는지 여부 체크
        self.angle_degree:float=90
            # 발사 각도
        self.speed:int=BUBBLE_SPEED
            # 이동 속도
        self.row_idx:int=-1
            # 격자 행 인덱스: 격자에 배치되지 않은 상태로 초기화(-1)
        self.col_idx:int=-1
            # 격자 행 인덱스: 격자에 배치되지 않은 상태로 초기화(-1)

    # 버블을 화면에 그림.
    def draw(self,screen:pygame.Surface)->None:
        # TODO: 색깔 딕셔너리를 써서 버블 원 그리기.
        # TODO: 테두리 추가해서 가독성 향상시키기.
        # 버블 원 그림.
        pygame.draw.circle(screen,COLORS[self.color],(int(self.x),int(self.y)),self.radius)
        # 흰색 테두리 추가해서 가독성 향상시킴.
        pygame.draw.circle(screen,(255,255,255),(int(self.x),int(self.y)),self.radius,2)

    # 발사 각도 설정함.
    def set_angle(self,angle_degree:float)->None:
        # TODO: 발사 각도 저장하기.
        self.angle_degree=angle_degree

    # 격자 인덱스 설정함.
    def set_grid_index(self,r:int,c:int)->None:
        # PARAMETERS: *r: row, *c: column
        # TODO: 행, 열 인덱스 저장하기.
        self.row_idx=r
        self.col_idx=c

    # 벽 반사 포함해서 발사된 버블 이동.
    def move(self)->None:
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
    def __init__(self,x:int,y:int)->None:
        self.x:int=x
            # 발사대 x 좌표
        self.y:int=y
            # 발사대 y 좌표
        self.angle:float=90
            # 발사 각도 (default: 위쪽)
        self.min_angle:float=10
            # 최소 각도 제한
        self.max_angle:float=170
            # 최대 각도 제한
        self.angle_speed:float=2.0
            # 회전 속도

    # 키보드 입력으로 각도 조정함.
    def rotate(self,delta:float)->None:
        # TODO: 각도 증감하고 나서 범위 제한하기 (clamp 사용해서)
        self.angle+=delta
        self.angle=clamp(self.angle,self.min_angle,self.max_angle)
            # 각도 범위 제한

    # 발사대 조준선 그리는 역할.
    def draw(self,screen:pygame.Surface)->None:
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
    def __init__(self,rows:int,cols:int,cell_size:int,wall_offset:int=0)->None:
        self.rows:int=rows
            # 격자 행 수
        self.cols:int=cols
            # 격자 열 수
        self.cell:int=cell_size
            # 셀 크기
        self.wall_offset:int=wall_offset
            # 벽 하강 오프셋
        self.map:List[List[str]]=[['.' for _ in range(cols)] for _ in range(rows)]
            # '.'으로 채워진 2차원 배열 생성
        self.bubble_list:List[Bubble]=[]
            # 화면에 있는 버블 리스트

    # 스테이지 맵 로드함.
    def load_from_stage(self,stage_map:List[List[str]])->None:
        # TODO: 맵 데이터를 읽어서 버블 만들기.
        # TODO: 각 버블에 격자 인덱스 할당하기.
        self.map=[row[:] for row in stage_map]
            # 원본 STAGES 데이터를 보호하기 위해 각 행 복사 후 2차원 리스트를 새로 만드는 로직
        self.bubble_list=[]
            # 기존 버블 객체 모두 제거함.

        for r in range(self.rows):
            for c in range(self.cols):
                if c<len(self.map[r]):
                    ch=self.map[r][c]
                else:
                    ch='.'

                # 딕셔너리 안에 키가 존재하는지 확인.
                if ch in COLORS:
                    x,y=self.get_cell_center(r,c)
                    b=Bubble(x,y,ch)
                    b.is_attached=True
                    b.set_grid_index(r,c)
                    self.bubble_list.append(b)


    # 육각 격자의 중심 좌표를 계산함.
    def get_cell_center(self,r:int,c:int)->Tuple[int,int]:
        """육각형 격자 배열의 중심 좌표 계산함.

        육각형 배열은 지그재그 배열을 사용하기 때문에 이런 계산 로직을 사용함 → 육각 격자 체계의 핵심 로직

        Args:
            r (int): 행 인덱스
            c (int): 열 인덱스

        Returns:
            Tuple[int,int]: (x,y) 중심 좌표
        """
        # PARAMETERS: *r: row, *c: column
        # TODO: 짝수, 홀수 행에 따라서 다른 오프셋을 적용하기.
        # TODO: x, y 좌표 반환하기.

        x=c*self.cell+self.cell//2
        y=r*self.cell+self.cell//2+self.wall_offset
        # 홀수 행은 오른쪽으로 반 칸 이동.
        if r%2==1:
            x+=self.cell//2
        return x,y


    # 화면 좌표를 격자 인덱스로 바꿈.
    def screen_to_grid(self,x:float,y:float)->Tuple[int,int]:
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
    def place_bubble(self,bubble:Bubble,r:int,c:int)->None:
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
    def nearest_grid_to_point(self,x:float,y:float)->Tuple[int,int]:
        # TODO: 충돌 지점의 격자 인덱스를 계산함.
        # TODO: 이웃 중 빈 칸을 찾음.
        r,c=self.screen_to_grid(x,y)
            # input받은 좌표에서 가장 가까운 빈 격자 찾음.

        # 이 위치에 이미 버블이 있거나 슬래시 문자가 있는 경우
        if self.map[r][c] in COLORS or self.map[r][c]=='/':
            neighbors=self.get_neighbors(r,c)
            # 각 neighbor 순회하면서 빈칸 찾으면 바로 반환
            for nr,nc in neighbors:
                if self.is_in_bounds(nr,nc) and self.map[nr][nc]=='.':
                    return nr,nc

        # 빈 칸 못 찾으면 경고 로그
        print(f"Warning: no empty cell found near. ({r},{c})")
        return r,c

    # 격자 범위를 체크함.
    def is_in_bounds(self,r:int,c:int)->bool:
        # TODO: 행, 열이 맵 범위 내에 있는지 확인하기.
        return 0<=r<self.rows and 0<=c<self.cols


    def get_neighbors(self,r:int,c:int)->List[Tuple[int,int]]:
        """육각 격자의 6개 이웃 좌표를 반환함.

        Args:
            r (int): 현재 버블의 행(row) 인덱스
            c (int): 현재 버블의 열(column) 인덱스

        Returns:
            List[Tuple[int, int]]: 인접한 6개 셀의 (행, 열) 좌표 리스트.
                                    좌, 좌상, 우상, 우, 우하, 좌하 순서로 반환됨.
        """
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
    def dfs_same_color(self,row:int,col:int,color:str,visited:Set[Tuple[int,int]])->None:
        """같은 색깔 버블을 스택 기반으로 한 DFS로 탐색함.

        Args:
            row (int): _description_
            col (int): _description_
            color (str): _description_
            visited (Set[Tuple[int,int]]): 방문한 셀 집합
        """
        # TODO: 재귀적으로 같은 색깔 버블 찾기.
        # TODO: `visited` 집합에 좌표 추가하기.
        stack=[(row,col)]

        while stack:
            r,c=stack.pop()

            if not self.is_in_bounds(r,c):
                continue
            if self.map[r][c]!=color:
                continue
            if (r,c) in visited:
                continue

            visited.add((r,c))

            for nr,nc in self.get_neighbors(r,c):
                stack.append((nr,nc))

    # 특정 셀 제거함.
    def remove_cells(self,cells:Set[Tuple[int,int]])->None:
        """특정 셀 제거함.

        Args:
            cells (Set[Tuple[int,int]]): 제거할 셀의 좌표 집합
        """
        # TODO: 맵에서 제거하기. ('.' 처리)
        # TODO: bubble_list에서 제거하기.
        cell_set=set(cells)
        for (r,c) in cell_set:
            self.map[r][c]='.'
                # 맵에서 제거함.

        self.bubble_list=[
            b for b in self.bubble_list
            if (b.row_idx,b.col_idx) not in cell_set
        ]

    # 천장과 연결된 버블을 찾음. (DFS)
    def flood_from_top(self)->Set[Tuple[int,int]]:
        """천장과 연결된 버블 찾음. (DFS 적용해서)

        Returns:
            Set[Tuple[int,int]]: 천장이랑 연결된 셀 좌표 집합
        """
        # TODO: 첫 번째 행에서 DFS 시작하기.
        # TODO: 연결된 버블 집합 반환하기.
        visited: Set[Tuple[int,int]]=set()

        # DFS 시작
        for c in range(self.cols):
            if self.map[0][c] in COLORS:
                self._dfs_reachable(0,c,visited)

        return visited



    # 천장 연결 DFS를 수행함.
    def _dfs_reachable(self,row:int,col:int,visited:Set[Tuple[int,int]])->None:
        """천장 연결 DFS
        재귀적으로 연결된 모든 버블 찾음.

        Args:
            row (int): _description_
            col (int): _description_
            visited (Set[Tuple[int,int]]): _description_
        """
        # TODO: 재귀적으로 천장과 연결된 버블 탐색하기.
        if not self.is_in_bounds(row,col):
            return

        # 버블이 아니면
        if self.map[row][col] not in COLORS:
            return

        # 이미 방문했으면
        if (row,col) in visited:
            return

        visited.add((row,col))
            # 방문 표시함.

        for nr,nc in self.get_neighbors(row,col):
            self._dfs_reachable(nr,nc,visited)


    # 천장과 연결되지 않은 버블을 제거함. (자유낙하)
    def remove_hanging(self)->None:
        # TODO: 천장 연결 버블 찾기.
        # TODO: 연결되지 않은 버블 삭제하기.
        # 연결된 것들
        connected=self.flood_from_top()

        # 연결 안 된 것들
        not_connected:List[Tuple[int,int]]=[]

        for r in range(self.rows):
            for c in range(self.cols):
                if self.map[r][c] in COLORS and (r,c) not in connected:
                    not_connected.append((r,c))
        if not_connected:
            self.remove_cells(set(not_connected))

    # 모든 버블을 그림.
    def draw(self,screen:pygame.Surface)->None:
        """모든 버블 그림.

        Args:
            screen (pygame.Surface): 그릴 화면 표면(Surface)
        """
        # TODO: bubble_list에 들어있는 모든 버블 draw() 호출하기.
        for b in self.bubble_list:
            b.draw(screen)

    # 벽 하강시킴. (4발 발사한 뒤)
    def drop_wall(self)->None:
        """벽 하강(4발 발사하고 나서):

        벽 한 칸 내려오면서 난이도 또한 증가.
        """
        # TODO: wall_offset 증가시키기.
        # TODO: 모든 버블 위치 재계산하기.
        self.wall_offset+=WALL_DROP_PIXELS
            # 오프셋 증가

        # 모든 버블 위치 같이 내림.
        for b in self.bubble_list:
            cx,cy=self.get_cell_center(b.row_idx,b.col_idx)
            b.x,b.y=cx,cy

        # if self.lowest_bubble_bottom()>self.cannon.y-CELL_SIZE*0.5:
        #     self.running=False

# ======== ScoreDisplay 클래스 - 점수 표시 ========
class ScoreDisplay:
    """ 게임의 현재 점수를 표시하는 UI. """
    def __init__(self)->None:
        self.score:int=0
            # 초기 점수
        self.font:pygame.font.Font=pygame.font.Font(None,40)
            # 폰트

    # 점수 추가함.
    def add(self,points:int)->None:
        # TODO: 점수 증가시키기.
        """점수 추가함

        Args:
            points (int): 추가할 점수
        """
        self.score+=points

    # 점수를 화면에 표시함.
    def draw(self,screen:pygame.Surface)->None:
        # TODO: 점수 텍스트 렌더링하고 화면 출력하기.
        """점수 표시 그림.

        Args:
            screen (pygame.Surface): 그릴 화면 표면(pygame.Surface)
        """
        txt=self.font.render(f'Score: {self.score}',True,(255,255,255))

        # 보기 편하게 반투명 배경 추가
        padding=10
        bg_rectangle=txt.get_rect()
        bg_rectangle.x=20-padding
        bg_rectangle.y=20-padding
        bg_rectangle.width+=padding*2
        bg_rectangle.height+=padding*2

        bg_surface=pygame.Surface((bg_rectangle.width,bg_rectangle.height))
        bg_surface.set_alpha(UI_ALPHA)
            # value를 180으로 해서 반투명 적용
        bg_surface.fill((0,0,0))
            # 검은색으로

        screen.blit(bg_surface,(bg_rectangle.x,bg_rectangle.y))
            # 배경 그림.
        screen.blit(txt,(20,20))


# ======== Game 클래스 - 메인 게임 로직 ========
class Game:
    """ 게임의 전체 로직을 관리하는 메인 클래스임. 초기화, 업데이트, 그리기, 이벤트 처리를 담당함. """
    def __init__(self)->None:
        # 화면 설정
        self.screen:pygame.Surface=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
            # 게임 화면
        pygame.display.set_caption("Bubble Pop MVP")
            # 게임 창의 제목 표시줄에 표시될 텍스트 설정
        self.clock:pygame.time.Clock=pygame.time.Clock()
            # 게임 프레임 속도 제어하는 로직 (Clock 객체 생성)
        self.grid:HexGrid=HexGrid(MAP_ROWS,MAP_COLS,CELL_SIZE,wall_offset=0)
            # 육각 격자 객체

        # 게임 오브젝트 초기화
        self.cannon:Cannon=Cannon(SCREEN_WIDTH//2,SCREEN_HEIGHT-120)
            # 화면 하단 중간에 배치해놓기.

        # 게임 오버 라인 정의
            # 발사대보다 1-2칸 위로 지정
        self.game_over_line=self.cannon.y-CELL_SIZE*0.5

        self.score_ui:ScoreDisplay=ScoreDisplay()
            # 점수 UI 객체

        # 게임 상태
        self.current_stage:int=0
            # 현재 스테이지 인덱스
        self.current_bubble:Optional[Bubble]=None
            # 현재 발사할 버블
        self.next_bubble:Optional[Bubble]=None
            # 다음 버블 (미리보기)
        self.fire_in_air:bool=False
            # 발사 중인지 여부
        self.fire_count:int=0
            # 발사 횟수 (4발마다 벽 하강함)
        # self.prepare_bubbles
            # 처음 버블 준비

        self.running:bool=True
            # 게임 실행 여부

        self.load_stage(self.current_stage)

    # 스테이지 로드함.
    def load_stage(self,stage_index:int)->None:
        """스테이지 로드함.

        Args:
            stage_index (int): 로드할 스테이지 인덱스
        """
        # TODO: STAGES에서 맵 데이터 가져오기.
        # TODO: grid.load_from_stage() 호출하기.
        # TODO: 초기 버블 준비하기.
        stage_map=STAGES[stage_index]
        # 오프셋 초기화
        self.grid.wall_offset=0

        self.grid.load_from_stage(stage_map)
            # 맵 로드

        # 전체 초기화
        self.current_bubble=None
        self.next_bubble=None
        self.fire_in_air=False
        self.fire_count=0

        self.prepare_bubbles()
            # 초기 버블 준비.

    # 맵에 존재하는 색깔 중 랜덤 선택함.
    def random_color_from_map(self)->str:
        # TODO: 맵을 순회하면서 존재하는 색깔 수집하기.
        # TODO: random.choice()로 선택하기.
        colors=set()
            # 빈 집합 생성

        for r in range(self.grid.rows):
            for c in range(min(self.grid.cols,len(self.grid.map[r]))):
                ch=self.grid.map[r][c]
                    # 색상 추출
                if ch in COLORS:
                    colors.add(ch)
        # 맵에 버블이 없으면 모든 색깔 사용 가능하도록 설정함.
        if not colors:
            colors=set(COLORS.keys())
        return random.choice(list(colors))


    # 새 버블 생성함.
    def create_bubble(self)->Bubble:
        # TODO: random_color_from_map()로 색깔 선택하기.
        # TODO: Bubble 인스턴스 생성하기.
        color=self.random_color_from_map()
        b=Bubble(self.cannon.x,self.cannon.y,color)
        return b

    # 현재, 다음 버블 준비함.
    def prepare_bubbles(self)->None:
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
    def process_collision_and_attach(self)->bool:
        # TODO: 천장 충돌 체크하기.
        # TODO: 기존 버블과 충돌 체크하기. (거리 계산)
        # TODO: 충돌 시 place_bubble() 호출하기.
        if self.current_bubble is None:
            return False
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
    def pop_if_match(self,row:int,col:int)->int:
        """3개 이상 붙으면 터뜨림.

        Args:
            row (int): 부착된 버블 위치
            col (int): 부착된 버블 위치

        Returns:
            int: 터진 버블 개수
        """
        # TODO: DFS로 같은 색깔 버블 찾기.
        # TODO: 3개 이상이면 제거하고 점수 추가하기.
        # TODO: 자유낙하 버블 제거하기.
        if self.current_bubble is None:
            return 0
        color=self.grid.map[row][col]

        # 색상 아니면 무시
        if color not in COLORS:
            return 0
                # return 타입이 인티저라 '0'

        # DFS로 같은 색 버블 찾음
        visited=set()
        self.grid.dfs_same_color(row,col,color,visited)

        # 세 개 이상이면 터뜨리기.
        if len(visited)>=3:
            self.grid.remove_cells(visited)
                # 버블 제거함.
            self.grid.remove_hanging()
                # 자유낙하 버블 제거함.
            self.score_ui.add(len(visited)*10)
                # 점수 추가 (버블당 10점 추가)
            return len(visited)

        # 안 터지면
        return 0

    # 게임 로직 업데이트함.
    def update(self)->None:
        # TODO: 이벤트 처리하기. (키보드 입력)
        # TODO: 발사체 이동, 충돌 처리하기.
        # TODO: 4발마다 벽 하강시키기.
        # TODO: 스테이지 클리어, 게임 오버 체크하기.
        # 이벤트 큐에 쌓인 모든 이벤트를 가져옴.
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                self.running=False

            elif event.type==pygame.KEYDOWN:
                # if event.key==pygame.K_LEFT:
                #     self.cannon.rotate(+self.cannon.angle_speed)
                #         # 왼쪽 키 입력하면 반시계 방향으로 rotate
                # elif event.key==pygame.K_RIGHT:
                #     self.cannon.rotate(-self.cannon.angle_speed)
                #         # 오른쪽 키 입력하면 시계 방향으로 rotate
                if event.key==pygame.K_SPACE:
                    if self.current_bubble and not self.fire_in_air:
                        self.fire_in_air=True
                        self.current_bubble.in_air=True
                        self.current_bubble.set_angle(self.cannon.angle)

        # 방향키는 매 프레임 체크
        keys=pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.cannon.rotate(+self.cannon.angle_speed)
                # 반시계 방향
        if keys[pygame.K_RIGHT]:
            self.cannon.rotate(-self.cannon.angle_speed)
                # 시계 방향

        # 발사체 이동.
        if self.current_bubble and self.fire_in_air:
            self.current_bubble.move()

            # 화면 위로 벗어난 경우
            if self.current_bubble.y<-BUBBLE_RADIUS:
                self.fire_in_air=False
                self.prepare_bubbles()
                return

            # 충돌 처리 로직
            if self.process_collision_and_attach():
                # 붙여진 위치에서 매칭 검사함.
                rr,cc=self.current_bubble.row_idx,self.current_bubble.col_idx
                self.pop_if_match(rr,cc)

                # 발사 횟수 증가
                self.fire_count+=1

                # 4발마다 벽 하강함.
                if self.fire_count>=LAUNCH_COOLDOWN:
                    self.grid.drop_wall()
                    self.fire_count=0
                        # 초기화

                self.current_bubble=None
                self.fire_in_air=False

                self.prepare_bubbles()

        # 스테이지 클리어했는지 체크함.
        if self.is_stage_cleared():
            self.show_stage_clear()
            self.current_stage+=1

            # 모든 스테이지 클리어하면 게임 종료
            if self.current_stage>=len(STAGES):
                self.running=False
            else:
                self.load_stage(self.current_stage)

        # 게임 오버 조건 체크함.
        if self.lowest_bubble_bottom()>self.game_over_line:
            self.running=False

    # 스테이지 클리어 여부 확인함.
    def is_stage_cleared(self)->bool:
        """스테이지 클리어 여부 확인함.

        Returns:
            bool: 클리어 여부
        """
        # TODO: 맵에 버블이 남아있는지 체크하기.
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                if self.grid.map[r][c] in COLORS:
                    return False
                        # 버블이 남아있으면 안 됨.
        return True
            # 모든 버블 없으면

    # 가장 아래 버블의 y좌표 구함.
    def lowest_bubble_bottom(self)->int:
        """가장 아래 버블 y좌표 구함.

        게임 오버 조건 체크하기 위해서.

        Returns:
            int: 가장 아래 버블 하단 y좌표
        """
        # TODO: bubble_list에서 최대 y 값 찾기.
        if not self.grid.bubble_list:
            return 0

        # 모든 버블의 하단 y좌표 수집해서 list로
        bottoms=[b.y+b.radius for b in self.grid.bubble_list]
        return max(bottoms)

    # 화면 그림.
    def draw(self)->None:
        """화면 그리기: 모든 UI 요소 포함함.
        """
        # TODO: 배경 색깔 채우기.
        # TODO: 격자, 발사대, 버블 그리기.
        # TODO: UI (점수, 다음 버블, 정보) 표시하기.
        self.screen.fill((10,20,30))
            # RGB 색상으로 채우기: 일단 임시로 어두운 파란색 배경

        # 내려올 벽 표현 (회색 영역으로)
        wall_y=self.grid.wall_offset
        pygame.draw.rect(
            self.screen,
            (80,80,80),
            (0,wall_y-SCREEN_HEIGHT,SCREEN_WIDTH,SCREEN_HEIGHT)
        )

        # 게임 오브젝트들
        self.grid.draw(self.screen)
            # 격자 버블
        self.cannon.draw(self.screen)
            # cannon

        # 현재 버블 그림.
        if self.current_bubble:
            self.current_bubble.draw(self.screen)

        # 다음 버블 미리보는 기능 구현
            # 왼쪽 하단에 두고 똑같이 보기 편하게 반투명으록 구현
        if self.next_bubble:
            # 기준점 먼저 설정
                # 다음 버블 그려질 중심 좌표
            next_x=80
            next_y=SCREEN_HEIGHT-100

            bg_surface=pygame.Surface((120,120))
            bg_surface.set_alpha(UI_ALPHA)
                # surface의 투명도 설정
            bg_surface.fill((0,0,0))
            self.screen.blit(bg_surface,(next_x-60,next_y-60))

            # NEXT 텍스트
            font=pygame.font.Font(None,32)
            next_txt=font.render("NEXT",True,(255,255,255))
            next_txt_rect=next_txt.get_rect(center=(next_x,next_y-40))
                # rect 객체 반환
            self.screen.blit(next_txt,next_txt_rect)

            # 다음 버블 그리기
            pygame.draw.circle(
                self.screen,
                COLORS[self.next_bubble.color],
                (next_x,next_y),
                self.next_bubble.radius
            )

            # 테두리
            pygame.draw.circle(
                self.screen,
                (255,255,255),
                (next_x,next_y),
                self.next_bubble.radius,
                2
            )

        self.score_ui.draw(self.screen)
            # 점수 표시.

        # 상단 중앙에 정보 ui 구현
        font=pygame.font.Font(None,40)
        info=f'Stage {self.current_stage+1}/{len(STAGES)} | Shots {self.fire_count}/{LAUNCH_COOLDOWN} | Angle {int(self.cannon.angle)}'
        info_txt=font.render(info,True,(220,220,220))
            # 밝은 회색으로 표시
        info_rect=info_txt.get_rect(center=(SCREEN_WIDTH//2,40))
            # 중심 좌표 지정

        # 반투명 배경 추가
        padding=15
            # 텍스트 주변에 15px 여백 둚.

        bg_rectangle=pygame.Rect(
            info_rect.x-padding,
            info_rect.y-padding,
            info_rect.width+padding*2,
            info_rect.height+padding*2
        )

        bg_surface=pygame.Surface((bg_rectangle.width, bg_rectangle.height))
        bg_surface.set_alpha(UI_ALPHA)
        bg_surface.fill((0,0,0))
        self.screen.blit(bg_surface,(bg_rectangle.x,bg_rectangle.y))
        self.screen.blit(info_txt,info_rect)




        pygame.display.flip()
            # 화면 갱신함.

    def show_stage_clear(self)->None:
        """스테이지 클리어 화면 표시
        """
        # 반투명한 오버레이
        overlay=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0,0,0))
        self.screen.blit(overlay,(0,0))

        # 텍스트
        font=pygame.font.Font(None,120)
        text=font.render('clear.',True,(100,255,100))
            # 연두색
        rect=text.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2))
        self.screen.blit(text,rect)

        # 스테이지 정보 (작은 글씨로)
        small_font=pygame.font.Font(None,50)
        info=small_font.render(
            f'Stage {self.current_stage} complete.',
            True,
            (200,200,200)
        )
        info_rect=info.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2+80))
        self.screen.blit(info,info_rect)

        pygame.display.flip()
        pygame.time.delay(1000)

    # 메인 게임 루프 실행함.
    def run(self)->None:
        """게임 메인 루프
        """
        # TODO: 승리, 패배 메시지 표시하기.
        while self.running:
            self.clock.tick(FPS)
                # 프레임 속도 제한함.
            self.update()
                # 게임 로직 업데이트.
            self.draw()
                # 화면 그림.

        # 종료 화면
        self.screen.fill((0,0,0))
        font=pygame.font.Font(None,100)

        # 승리, 패배 메시지
        if self.current_stage>=len(STAGES):
            msg="Good."
        else:
            msg="Bye."

        # 텍스트 렌더링하고 중앙 배치하기
        txt=font.render(msg,True,(255,255,255))
        rect=txt.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2))
        self.screen.blit(txt,rect)

        pygame.display.flip()
        pygame.time.delay(END_SCREEN_DELAY)
            # 대기함.

def main()->None:
    # 프로그램 시작점
    Game().run()
    pygame.quit()
    sys.exit()

if __name__=="__main__":
    main()
