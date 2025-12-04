import math
    # 거리 계산 위해
import random
    # 난수 생성 위해
import sys
    # 경로 조작 위해
import csv
    # CSV 파일 읽기 위해
import os
    # 파일 경로 존재 여부 확인 위해
from typing import List,Set,Tuple,Optional
    # 타입 힌트 위해

import pygame
    # 게임 라이브러리

from config import (
    SCREEN_WIDTH,SCREEN_HEIGHT,FPS,CELL_SIZE,BUBBLE_RADIUS,BUBBLE_SPEED,
    LAUNCH_COOLDOWN,WALL_DROP_PIXELS,MAP_ROWS,MAP_COLS,
    NEXT_BUBBLE_X,NEXT_BUBBLE_Y_OFFSET,SCALE
)
    # 설정값 임포트
from game_settings import (
    END_SCREEN_DELAY,POP_SOUND_VOLUME,TAP_SOUND_VOLUME
)
    # 게임 설정값 임포트
from asset_paths import ASSET_PATHS
from constants import BubbleColor,GameState,Itemtype
from color_settings import (COLORS,
                            COLOR_MAP)

from obstacle import Obstacle

from pathlib import Path
sys.path.append(str(Path(__file__).parent))
    # 상대경로 임포트 위해

# ======== 버블 이미지 로드 ========
try:
    BUBBLE_IMAGES:dict[str,pygame.Surface]={
        'R':pygame.image.load(ASSET_PATHS['bubble_red']),
        'Y':pygame.image.load(ASSET_PATHS['bubble_yellow']),
        'B':pygame.image.load(ASSET_PATHS['bubble_blue']),
        'G':pygame.image.load(ASSET_PATHS['bubble_green']),
    }
    print("버블 이미지 로드 완료.")
except pygame.error as e:
    print(f"이미지 로드 실패함: {e}. 기본 색상으로 대체합니다.")
    BUBBLE_IMAGES=None

# ======== 이미지 크기 조정 ========
if BUBBLE_IMAGES:
    target_size=BUBBLE_RADIUS*2
    for color in BUBBLE_IMAGES:
        BUBBLE_IMAGES[color]=pygame.transform.smoothscale(
            BUBBLE_IMAGES[color],
            (target_size,target_size)
        )
    print(f"버블 이미지 크기 조정 완료: {target_size}x{target_size}px")

# 안전차원에서 다시 명시
COLORS:dict[str,Tuple[int,int,int]]={
    'R':(220,50,50),
    'Y':(240,200,60),
    'B':(60,100,240),
    'G':(70,200,120),
}

# ======== 유틸리티 ========
def clamp(v:float,lo:float,hi:float)->float:
    return max(lo,min(hi,v))

def load_stage_from_csv(stage_index:int)->List[List[str]]:
    csv_path=f'assets/map_data/stage{stage_index+1}.csv'

    if not os.path.exists(csv_path):
        return [['.' for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]
            # 빈 맵 반환 (로드 안 되면 빈 맵으로 처리)

    stage_map=[]
    try:
        with open(csv_path,'r',encoding='utf-8') as f:
            reader=csv.reader(f)
            for row in reader:
                map_row=[]
                for cell in row:
                    cell=cell.strip()
                    if cell=='' or cell.upper()=='X':
                        map_row.append('.')
                    elif cell.upper()=='N':
                        map_row.append('N')
                    elif cell.upper() in COLORS:
                        map_row.append(cell.upper())
                    else:
                        map_row.append('.')
                while len(map_row)<MAP_COLS:
                    map_row.append('.')
                map_row=map_row[:MAP_COLS]
                stage_map.append(map_row)

        while len(stage_map)<MAP_ROWS:
            stage_map.append(['.' for _ in range(MAP_COLS)])
        stage_map=stage_map[:MAP_ROWS]

        print(f"스테이지 {stage_index+1} 맵 데이터 로드 완료: {csv_path}")
        return stage_map

    except Exception as e:
        print(f"오류: {csv_path} 파일을 읽는 중 오류가 발생했습니다: {e}")
        return [['.' for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]

# ======== Bubble ========
class Bubble:
    def __init__(self,x:float,y:float,color:str,radius:int=BUBBLE_RADIUS)->None:
        self.x:float=x
        self.y:float=y
        self.color:str=color
        self.radius:int=radius
        self.in_air:bool=False
        self.is_attached:bool=False
        self.angle_degree:float=90
        self.speed:int=BUBBLE_SPEED
        self.row_idx:int=-1
        self.col_idx:int=-1

    def draw(self,screen:pygame.Surface)->None:
        if BUBBLE_IMAGES:
            img=BUBBLE_IMAGES[self.color]
            rect=img.get_rect(center=(int(self.x),int(self.y)))
            screen.blit(img,rect)
        else:
            pygame.draw.circle(screen,COLORS[self.color],(int(self.x),int(self.y)),self.radius)
            pygame.draw.circle(screen,(255,255,255),(int(self.x),int(self.y)),self.radius,2)

    def set_angle(self,angle_degree:float)->None:
        self.angle_degree=angle_degree

    def set_grid_index(self,r:int,c:int)->None:
        self.row_idx=r
        self.col_idx=c

    def move(self)->None:
        rad=math.radians(self.angle_degree)
        dx=self.speed*math.cos(rad)
        dy=-self.speed*math.sin(rad)
        self.x+=dx
        self.y+=dy

        grid_x_start=(SCREEN_WIDTH-(MAP_COLS*CELL_SIZE))//2
        grid_x_end=grid_x_start+(MAP_COLS*CELL_SIZE)

        if self.x-self.radius<grid_x_start:
            self.x=grid_x_start+self.radius
            self.angle_degree=180-self.angle_degree
        elif self.x+self.radius>grid_x_end:
            self.x=grid_x_end-self.radius
            self.angle_degree=180-self.angle_degree

# ======== Cannon ========
class Cannon:
    def __init__(self,x:int,y:int)->None:
        self.x:int=x
        self.y:int=y
        self.angle:float=90
        self.min_angle:float=10
        self.max_angle:float=170
        self.angle_speed:float=4.0

        try:
            self.arrow_image=pygame.image.load(ASSET_PATHS['cannon_arrow']).convert_alpha()
            self.arrow_image=pygame.transform.smoothscale(self.arrow_image,(152,317))
        except pygame.error:
            print("발사대 이미지 로드 실패")
            self.arrow_image=None

    def rotate(self,delta:float)->None:
        self.angle+=delta
        self.angle=clamp(self.angle,self.min_angle,self.max_angle)

    def draw(self,screen:pygame.Surface)->None:
        if self.arrow_image:
            rotated_arrow=pygame.transform.rotate(self.arrow_image,self.angle-90)
            arrow_rect=rotated_arrow.get_rect(center=(self.x,self.y))
            screen.blit(rotated_arrow,arrow_rect)
        else:
            length=100
            rad=math.radians(self.angle)
            end_x=self.x+length*math.cos(rad)
            end_y=self.y-length*math.sin(rad)
            pygame.draw.line(screen,(255,255,255),(self.x,self.y),(end_x,end_y),4)
            pygame.draw.circle(screen,(255,0,0),(self.x,self.y),6)

# ======== HexGrid ========
class HexGrid:
    def __init__(self,rows:int,cols:int,cell_size:int,wall_offset:int=0,
                 x_offset:int=0,y_offset:int=0)->None:
        self.rows:int=rows
        self.cols:int=cols
        self.cell:int=cell_size
        self.wall_offset:int=wall_offset
        self.x_offset:int=x_offset
        self.y_offset:int=y_offset
        self.map:List[List[str]]=[['.' for _ in range(cols)] for _ in range(rows)]
        self.bubble_list:List[Bubble]=[]
        self.obs_list:List[Obstacle]=[]

    def load_from_stage(self,stage_map:List[List[str]])->None:
        self.map=[row[:] for row in stage_map]
        self.bubble_list=[]
        self.obs_list=[]
        for r in range(self.rows):
            if r>=len(self.map):
                break
            for c in range(self.cols):
                if c<len(self.map[r]):
                    ch=self.map[r][c]
                else:
                    ch='.'

                # 버블 파싱
                if ch in COLORS:
                    x,y=self.get_cell_center(r,c)
                    b=Bubble(x,y,ch)
                    b.is_attached=True
                    b.set_grid_index(r,c)
                    self.bubble_list.append(b)
                    continue

                # 장애물 파싱
                if ch=='N':
                    obsx,obsy=self.get_cell_center(r,c)
                    # ob=Obstacle(obsx,obsy,BUBBLE_RADIUS)
                    ob=Obstacle(obsx,obsy,BUBBLE_RADIUS,r,c)
                    self.obs_list.append(ob)
                    self.map[r][c]='N'
                    continue

    def get_cell_center(self,r:int,c:int)->Tuple[int,int]:
        x=c*self.cell+self.cell//2+self.x_offset
        y=r*self.cell+self.cell//2+self.wall_offset+self.y_offset
        if r%2==1:
            x+=self.cell//2
        return x,y

    def screen_to_grid(self,x:float,y:float)->Tuple[int,int]:
        r=int((y-self.wall_offset-self.y_offset)//self.cell)
        if r<0:
            r=0
        c_base=x-self.x_offset
        if r%2==1:
            c=int((c_base-self.cell//2)//self.cell)
        else:
            c=int(c_base//self.cell)
        c=clamp(c,0,self.cols-1)
        r=clamp(r,0,self.rows-1)
        return int(r),int(c)

    def place_bubble(self,bubble:Bubble,r:int,c:int)->None:
        if r<0 or r>=self.rows or c<0 or c>=self.cols:
            print(f"Error: Out of bounds placement at ({r},{c})")
            return

        if self.map[r][c]=='/':
            c=clamp(c+1,0,self.cols-1)

        if r>=len(self.map) or c>=len(self.map[r]):
            print(f"Warning: Placing bubble at ({r},{c}) which may be out of map data bounds.")

        self.map[r][c]=bubble.color
        cx,cy=self.get_cell_center(r,c)
        bubble.x,bubble.y=cx,cy
        bubble.is_attached=True
        bubble.in_air=False
        bubble.set_grid_index(r,c)
        self.bubble_list.append(bubble)

    def nearest_grid_to_point(self,x:float,y:float)->Tuple[int,int]:
        r,c=self.screen_to_grid(x,y)

        if not self.is_in_bounds(r,c):
            return (0,clamp(c,0,self.cols-1))

        if self.map[r][c] in COLORS or self.map[r][c]=='/':
            neighbors=self.get_neighbors(r,c)
            best_neighbor=(r,c)
            min_dist_sq=float('inf')
            found_empty=False

            for nr,nc in neighbors:
                if self.is_in_bounds(nr,nc) and self.map[nr][nc]=='.':
                    nx,ny=self.get_cell_center(nr,nc)
                    dist_sq=(x-nx)**2+(y-ny)**2
                    if dist_sq<min_dist_sq:
                        min_dist_sq=dist_sq
                        best_neighbor=(nr,nc)
                        found_empty=True

            if found_empty:
                return best_neighbor

        if self.is_in_bounds(r,c) and self.map[r][c]=='.':
            return r,c

        print(f"Warning: no empty cell found near. ({r},{c}). Forcing.")
        return r,c

    def is_in_bounds(self,r:int,c:int)->bool:
        return 0<=r<self.rows and 0<=c<self.cols

    def get_neighbors(self,r:int,c:int)->List[Tuple[int,int]]:
        if r%2==0:
            dr=[0,-1,-1,0,1,1]
            dc=[-1,-1,0,1,0,-1]
        else:
            dr=[0,-1,-1,0,1,1]
            dc=[-1,0,1,1,1,0]
        return [(r+dr[i],c+dc[i]) for i in range(6)]

    def dfs_same_color(self,row:int,col:int,color:str,visited:Set[Tuple[int,int]])->None:
        stack=[(row,col)]
        while stack:
            r,c=stack.pop()
            if not self.is_in_bounds(r,c) or (r,c) in visited:
                continue
            if r>=len(self.map) or c>=len(self.map[r]):
                continue
            if self.map[r][c]!=color:
                continue
            visited.add((r,c))
            for nr,nc in self.get_neighbors(r,c):
                stack.append((nr,nc))

    def remove_cells(self,cells:Set[Tuple[int,int]])->None:
        cell_set=set(cells)
        for (r,c) in cell_set:
            if self.is_in_bounds(r,c):
                self.map[r][c]='.'
        self.bubble_list=[
            b for b in self.bubble_list
            if (b.row_idx,b.col_idx) not in cell_set
        ]

    def flood_from_top(self)->Set[Tuple[int,int]]:
        visited:Set[Tuple[int,int]]=set()
        for c in range(self.cols):
            if 0<len(self.map) and c<len(self.map[0]):
                if self.map[0][c] in COLORS:
                    self._dfs_reachable(0,c,visited)
        return visited

    def _dfs_reachable(self,row:int,col:int,visited:Set[Tuple[int,int]])->None:
        if not self.is_in_bounds(row,col) or (row,col) in visited:
            return
        if row>=len(self.map) or col>=len(self.map[row]):
            return
        if self.map[row][col] not in COLORS:
            return
        visited.add((row,col))
        for nr,nc in self.get_neighbors(row,col):
            self._dfs_reachable(nr,nc,visited)

    def remove_hanging(self)->None:
        connected=self.flood_from_top()
        not_connected:List[Tuple[int,int]]=[]
        for r in range(self.rows):
            if r>=len(self.map):
                break
            for c in range(self.cols):
                if c>=len(self.map[r]):
                    break
                if self.map[r][c] in COLORS and (r,c) not in connected:
                    not_connected.append((r,c))
        if not_connected:
            self.remove_cells(set(not_connected))

    def draw(self,screen:pygame.Surface)->None:
        for b in self.bubble_list:
            b.draw(screen)

        for ob in self.obs_list:
            ob.draw(screen)

    def drop_wall(self)->None:
        self.wall_offset+=WALL_DROP_PIXELS
        for b in self.bubble_list:
            cx,cy=self.get_cell_center(b.row_idx,b.col_idx)
            b.x,b.y=cx,cy

        for ob in self.obs_list:
            cx,cy=self.get_cell_center(ob.row_idx,ob.col_idx)
            ob.x,ob.y=cx,cy

    def raise_wall(self)->None:
        """벽을 한 칸 올려서(위로 이동) 여유 공간 늘림.
        """
        if self.wall_offset<=0:
            # 더 이상 못 올리면
            return
        self.wall_offset=max(0,self.wall_offset-WALL_DROP_PIXELS)
        for b in self.bubble_list:
            cx,cy=self.get_cell_center(b.row_idx,b.col_idx)
            b.x,b.y=cx,cy

        for ob in self.obs_list:
            cx,cy=self.get_cell_center(ob.row_idx,ob.col_idx)
            ob.x,ob.y=cx,cy

# ======== ScoreDisplay ========
class ScoreDisplay:
    def __init__(self)->None:
        self.score:int=0
        try:
            self.font=pygame.font.Font(ASSET_PATHS['font'],50)
        except:
            print("픽셀 폰트 로드 실패. 기본 폰트로 대체합니다.")
            self.font=pygame.font.Font(None,50)

    def add(self,points:int)->None:
        self.score+=points

    def draw(self,screen:pygame.Surface,level:int)->None:
        score_txt=self.font.render(f'SCORE : {self.score}',True,(0,0,0))
        level_txt=self.font.render(f'LEVEL : {level}',True,(0,0,0))
        screen.blit(score_txt,(30,30))
        screen.blit(level_txt,(30,80))

# ======== Game ========
class Game:
    def __init__(self)->None:
        self.screen:pygame.Surface=pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
        pygame.display.set_caption("Bubble Pop (K-Univ. Edition)")
        self.clock:pygame.time.Clock=pygame.time.Clock()

        map_pixel_width=(MAP_COLS*CELL_SIZE)+(CELL_SIZE//2)
        self.grid_x_offset=((SCREEN_WIDTH-map_pixel_width)//2)+int(25*SCALE)
        self.grid_y_offset=int(30*SCALE)

        padding=int(10*SCALE)
        game_area_w=map_pixel_width+(padding*2)
        game_area_h=SCREEN_HEIGHT-self.grid_y_offset
        game_area_x=(SCREEN_WIDTH-game_area_w)//2
        game_area_y=self.grid_y_offset-padding
        self.game_rect=pygame.Rect(game_area_x,game_area_y,game_area_w,game_area_h)

        self.grid:HexGrid=HexGrid(MAP_ROWS,MAP_COLS,CELL_SIZE,
                                  0,
                                  self.grid_x_offset,self.grid_y_offset)

        cannon_x=self.game_rect.centerx
        cannon_y=self.game_rect.bottom-int(170*SCALE)
        self.cannon:Cannon=Cannon(cannon_x,cannon_y)

        self.game_over_line=self.cannon.y-CELL_SIZE*0.5
        self.score_ui:ScoreDisplay=ScoreDisplay()

        try:
            self.background_image=pygame.image.load(ASSET_PATHS['background']).convert()
            self.background_image=pygame.transform.scale(self.background_image,(SCREEN_WIDTH,SCREEN_HEIGHT))

            self.char_left=pygame.image.load(ASSET_PATHS['char_left']).convert_alpha()
            self.char_right=pygame.image.load(ASSET_PATHS['char_right']).convert_alpha()
            self.logo=pygame.image.load(ASSET_PATHS['logo']).convert_alpha()

            # SCALE 적용하여 화면 크기에 따라 조정
            self.char_left=pygame.transform.smoothscale(self.char_left,(int(313*SCALE),int(546*SCALE)))
            self.char_right=pygame.transform.smoothscale(self.char_right,(int(308*SCALE),int(555*SCALE)))
            self.logo=pygame.transform.smoothscale(self.logo,(int(176*SCALE),int(176*SCALE)))

        except pygame.error as e:
            print(f"배경/UI 이미지 로드 실패: {e}")
            self.background_image=None
            self.char_left=None
            self.char_right=None
            self.logo=None

        try:
            pygame.mixer.music.load(ASSET_PATHS['bgm'])
            pygame.mixer.music.set_volume(0.1)
            pygame.mixer.music.play(-1)
            print("BGM 재생 시작")
        except pygame.error as e:
            print(f"BGM 로드 실패: {e}")

        self.pop_sounds=[]
        for sound_path in ASSET_PATHS['pop_sounds']:
            try:
                sound=pygame.mixer.Sound(sound_path)
                sound.set_volume(POP_SOUND_VOLUME)
                self.pop_sounds.append(sound)
            except pygame.error as e:
                print(f"효과음 로드 실패: {sound_path} - {e}")

        if not self.pop_sounds:
            print("경고: 효과음 파일을 찾을 수 없습니다.")

        try:
            self.tap_sound=pygame.mixer.Sound(ASSET_PATHS['tap_sound'])
            self.tap_sound.set_volume(TAP_SOUND_VOLUME)
        except pygame.error as e:
            print(f"tap 효과음 로드 실패: {ASSET_PATHS['tap_sound']} - {e}")
            self.tap_sound=None

        self.current_stage:int=0
        self.current_bubble:Optional[Bubble]=None
        self.next_bubble:Optional[Bubble]=None
        self.fire_in_air:bool=False
        self.fire_count:int=0
        self.running:bool=True
        # --- 특수 아이템 개수 설정 (임시: 테스트용) ---
        self.item_swap_count:int=3
            # 버블 스왑 아이템 개수
        self.item_raise_count:int=3
            # 벽 한 줄 올리기 아이템 개수
        self.item_rainbow_count:int=3
            # 무지개 버블 아이템 개수
        # ------------------------------------------

        # --- 요청 플래그만 추가 (임시: 테스트용) ---
            # 플래그 방식 안 쓸 예정.

        # FIXME: UI용 폰트
        self.ui_font=pygame.font.SysFont('malgungothic',20)

        # 아이템 이미지 로드 (SCALE 적용)
        self.item_images = {}
        item_size = (int(80*SCALE), int(80*SCALE))  # 버튼 크기에 맞춤
        
        try:
            swap_img = pygame.image.load(ASSET_PATHS['item_swap']).convert_alpha()
            self.item_images['swap'] = pygame.transform.smoothscale(swap_img, item_size)
        except (pygame.error, FileNotFoundError) as e:
            print(f"SWAP 아이템 이미지 로드 실패: {e}")
            self.item_images['swap'] = None
        
        try:
            raise_img = pygame.image.load(ASSET_PATHS['item_raise']).convert_alpha()
            self.item_images['raise'] = pygame.transform.smoothscale(raise_img, item_size)
        except (pygame.error, FileNotFoundError) as e:
            print(f"RAISE 아이템 이미지 로드 실패: {e}")
            self.item_images['raise'] = None
        
        try:
            rainbow_img = pygame.image.load(ASSET_PATHS['item_rainbow']).convert_alpha()
            self.item_images['rainbow'] = pygame.transform.smoothscale(rainbow_img, item_size)
        except (pygame.error, FileNotFoundError) as e:
            print(f"RAINBOW 아이템 이미지 로드 실패: {e}")
            self.item_images['rainbow'] = None

        # 아이템 버튼 초기화
        self.init_item_buttons()

        self.load_stage(self.current_stage)

    def load_stage(self,stage_index:int)->None:
        stage_map=load_stage_from_csv(stage_index)

        if not stage_map or all(all(cell=='.' for cell in row) for row in stage_map):
            next_csv_path=f'assets/map_data/stage{stage_index+2}.csv'
            if not os.path.exists(next_csv_path):
                self.running=False
                return

        self.grid.wall_offset=0
        self.grid.y_offset=self.grid_y_offset

        self.grid.load_from_stage(stage_map)

        self.current_bubble=None
        self.next_bubble=None
        self.fire_in_air=False
        self.fire_count=0

        self.prepare_bubbles()

    def random_color_from_map(self)->str:
        colors=set()
        for bubble in self.grid.bubble_list:
            if bubble.color in COLORS:
                colors.add(bubble.color)
        if not colors:
            colors=set(COLORS.keys())
        return random.choice(list(colors))

    def create_bubble(self)->Bubble:
        color=self.random_color_from_map()
        b=Bubble(self.cannon.x,self.cannon.y,color)
        return b

    def prepare_bubbles(self)->None:
        if self.next_bubble is not None:
            self.current_bubble=self.next_bubble
        else:
            self.current_bubble=self.create_bubble()
        self.current_bubble.x,self.current_bubble.y=self.cannon.x,self.cannon.y
        self.current_bubble.in_air=False
        self.next_bubble=self.create_bubble()

    def init_item_buttons(self)->None:
        # SCALE 적용
        btn_w, btn_h = int(80*SCALE), int(80*SCALE)
        padding = int(12*SCALE)
        x = SCREEN_WIDTH - btn_w - int(40*SCALE)
        y0 = int(200*SCALE)  # 아이템 버튼 시작 Y 좌표 (아래로 이동)

        self.item_buttons=[
            {'type':'swap',
             'rect':pygame.Rect(x, y0 + 0*(btn_h+padding), btn_w, btn_h)},
            {'type':'raise',
             'rect': pygame.Rect(x, y0 + 1*(btn_h+padding), btn_w, btn_h)},
            {'type':'rainbow',
             'rect': pygame.Rect(x, y0 + 2*(btn_h+padding), btn_w, btn_h)},
        ]

        # 버튼 눌림 연출용 타이머 구현 (ms 단위로)
        self.item_button_pressed_until={
            'swap':0,
            'raise':0,
            'rainbow':0,
        }

    def handle_mouse_click(self,pos:Tuple[int,int])->None:
        mx,my=pos
        for btn in self.item_buttons:
            if btn['rect'].collidepoint(mx,my):
                self.handle_item_button_click(btn['type'])
                break

    def handle_item_button_click(self,item_type:str)->None:
        # 아이템 수량 0개면 그냥 무시
        if item_type=='swap' and self.item_swap_count<=0:
            print("No SWAP items left.")
            return
        if item_type=='raise' and self.item_raise_count<=0:
            print("No RAISE items left.")
            return
        if item_type=='rainbow' and self.item_rainbow_count<=0:
            print("No RAINBOW items left.")
            return

        # 로직 적용 (UI 클릭하면 그 순간 바로 효과 반영함)
        if item_type=='swap':
            self.use_item_swap()
        elif item_type=='raise':
            self.use_item_raise()
        elif item_type=='rainbow':
            self.use_item_rainbow()

        # 버튼 눌림 연출용 타이머 설정 (120ms 정도 유지)
        now=pygame.time.get_ticks()
        self.item_button_pressed_until[item_type]=now+120

    def draw_item_buttons(self,screen:pygame.Surface)->None:
        now=pygame.time.get_ticks()

        for btn in self.item_buttons:
            rect=btn['rect']
            item_type=btn['type']
            pressed=now<self.item_button_pressed_until[item_type]

            # 아이템 이미지가 있으면 이미지 사용, 없으면 기존 방식
            item_img = self.item_images.get(item_type)
            
            if item_img:
                # 이미지 표시
                screen.blit(item_img, rect)
                
                # 눌림 효과: 테두리 강조
                border_color = (255, 255, 100) if pressed else (220, 220, 220)
                border_w = 4 if pressed else 2
                pygame.draw.rect(screen, border_color, rect, border_w)
                
                # 남은 개수 표시 (이미지 위에)
                if item_type=='swap':
                    cnt=self.item_swap_count
                elif item_type=='raise':
                    cnt=self.item_raise_count
                else: # rainbow
                    cnt=self.item_rainbow_count
                
                # 개수를 오른쪽 하단에 표시
                cnt_surf=self.ui_font.render(str(cnt),True,(255,255,0))
                cnt_rect=cnt_surf.get_rect(bottomright=(rect.right-5, rect.bottom-5))
                
                # 개수 배경 (가독성 향상)
                bg_rect = cnt_rect.inflate(4, 4)
                pygame.draw.rect(screen, (0, 0, 0), bg_rect)
                screen.blit(cnt_surf, cnt_rect)
            else:
                # 이미지 없을 때 기존 방식 (텍스트)
                pygame.draw.rect(screen,(30,30,30),rect)
                border_w=4 if pressed else 2
                pygame.draw.rect(screen,(220,220,220),rect,border_w)

                # 라벨 + 남은 개수
                if item_type=='swap':
                    label='SWAP'
                    cnt=self.item_swap_count
                elif item_type=='raise':
                    label='RAISE'
                    cnt=self.item_raise_count
                else: # rainbow
                    label='RAIN'
                    cnt=self.item_rainbow_count

                text_surf=self.ui_font.render(label,True,(255,255,255))
                text_rect=text_surf.get_rect(center=(rect.centerx,rect.centery-14))
                screen.blit(text_surf,text_rect)

                cnt_surf=self.ui_font.render(str(cnt),True,(255,255,0))
                cnt_rect=cnt_surf.get_rect(center=(rect.centerx,rect.centery+18))
                screen.blit(cnt_surf,cnt_rect)

    def process_collision_and_attach(self)->bool:
        if self.current_bubble is None:
            return False

        if self.current_bubble.y-self.current_bubble.radius<=(
            self.grid.y_offset+self.grid.wall_offset
        ):
            r,c=self.grid.nearest_grid_to_point(self.current_bubble.x,self.current_bubble.y)
            r=0
            self.grid.place_bubble(self.current_bubble,r,c)

            popped_count=self.pop_if_match(r,c)
            if popped_count==0:
                if hasattr(self,'tap_sound') and self.tap_sound:
                    try:
                        self.tap_sound.play()
                    except:
                        pass
            return True

        for b in self.grid.bubble_list:
            dist=math.hypot(self.current_bubble.x-b.x,self.current_bubble.y-b.y)
            if dist<=self.current_bubble.radius+b.radius-2:
                r,c=self.grid.nearest_grid_to_point(self.current_bubble.x,self.current_bubble.y)
                self.grid.place_bubble(self.current_bubble,r,c)

                popped_count=self.pop_if_match(r,c)
                if popped_count==0:
                    if hasattr(self,'tap_sound') and self.tap_sound:
                        try:
                            self.tap_sound.play()
                        except:
                            pass
                return True

        # 장애물 충돌 검사
        for ob in self.grid.obs_list:
            dist=math.hypot(self.current_bubble.x-ob.x,self.current_bubble.y-ob.y)
            if dist<=self.current_bubble.radius+ob.radius-2:
                r,c=self.grid.nearest_grid_to_point(self.current_bubble.x,self.current_bubble.y)
                self.grid.place_bubble(self.current_bubble,r,c)

                # 장애물 근처에 붙어도 매칭 체크는 해야 함
                popped_count=self.pop_if_match(r,c)
                if popped_count==0:
                    if hasattr(self,'tap_sound') and self.tap_sound:
                        try:
                            self.tap_sound.play()
                        except:
                            pass

                return True

        return False

    def pop_if_match(self,row:int,col:int)->int:
        if self.current_bubble is None:
            return 0

        if not self.grid.is_in_bounds(row,col):
            return 0

        color=self.grid.map[row][col]
        if color not in COLORS:
            return 0

        visited=set()
        self.grid.dfs_same_color(row,col,color,visited)

        if len(visited)>=3:
            self.grid.remove_cells(visited)
            self.grid.remove_hanging()
            self.score_ui.add(len(visited)*10)

            if hasattr(self,'pop_sounds') and self.pop_sounds:
                random_sound=random.choice(self.pop_sounds)
                try:
                    random_sound.play()
                except:
                    pass

            return len(visited)
        return 0

    def update(self)->None:
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                self.running=False
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_SPACE:
                    if self.current_bubble and not self.fire_in_air:
                        self.fire_in_air=True
                        self.current_bubble.in_air=True
                        self.current_bubble.set_angle(self.cannon.angle)
                # --- 특수 아이템 테스트용 단축키 ---
                # FIXME: 키보드 1/2/3 --> 바로 아이템 사용
                # FIXME: 마우스 왼쪽 버튼 클릭 --> handle_mouse_click() 호출
                    # --> 버튼 클릭하면 아이템 사용
                elif event.key==pygame.K_1:
                    self.use_item_swap()
                elif event.key==pygame.K_2:
                    self.use_item_raise()
                elif event.key==pygame.K_3:
                    self.use_item_rainbow()

            elif event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                self.handle_mouse_click(event.pos)


        keys=pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.cannon.rotate(+self.cannon.angle_speed)
        if keys[pygame.K_RIGHT]:
            self.cannon.rotate(-self.cannon.angle_speed)

        if self.current_bubble and self.fire_in_air:
            self.current_bubble.move()

            if self.current_bubble.y<-BUBBLE_RADIUS:
                self.fire_in_air=False
                self.prepare_bubbles()
                return
            # --- 특수 아이템 플래그 처리(임시) ---
            # 플래그 방식 안 쓸 예정이라 지움.
            # AttributeError 터질 것 같음.
            # --------------------------
            if self.process_collision_and_attach():
                self.fire_count+=1
                if self.fire_count>=LAUNCH_COOLDOWN:
                    self.grid.drop_wall()
                    self.fire_count=0
                self.current_bubble=None
                self.fire_in_air=False
                self.prepare_bubbles()

        if self.is_stage_cleared():
            self.show_stage_clear()
            self.current_stage+=1
            next_csv_path=f'assets/map_data/stage{self.current_stage+1}.csv'
            if not os.path.exists(next_csv_path):
                self.running=False
                print("All stages cleared!")
            else:
                self.load_stage(self.current_stage)

        if self.lowest_bubble_bottom()>self.game_over_line:
            self.running=False
            print("Game Over")

    def is_stage_cleared(self)->bool:
        for r in range(self.grid.rows):
            if r>=len(self.grid.map):
                continue
            for c in range(self.grid.cols):
                if c>=len(self.grid.map[r]):
                    continue
                if self.grid.map[r][c] in COLORS:
                    return False
        return True

    def lowest_bubble_bottom(self)->int:
        if not self.grid.bubble_list:
            return 0
        bottoms=[b.y+b.radius for b in self.grid.bubble_list]
        return int(max(bottoms))

    def use_item_swap(self)->None:
        """현재 버블과 다음 버블 스왑함.
        """
        if self.item_swap_count<=0:
            print("No SWAP items left.")
            return
        if self.current_bubble is None or self.next_bubble is None:
            print("Cannot swap: one of the bubbles is missing.")
            return

        self.current_bubble.color,self.next_bubble.color\
            =self.next_bubble.color,self.current_bubble.color

        self.item_swap_count-=1
        print(f"SWAP used. Remaining: {self.item_swap_count}")

    def use_item_raise(self)->None:
        """벽을 한 줄 올림.
        """
        if self.item_raise_count<=0:
            print("No RAISE items left.")
            return

        # HexGrid에 위임
        before_offset=self.grid.wall_offset
        self.grid.raise_wall()

        if self.grid.wall_offset==before_offset:
            print("Cannot RAISE: wall is already at the top.")
            return

        self.item_raise_count-=1
        print(f"RAISE used. Remaining: {self.item_raise_count}")

    def best_color_for_rainbow(self)->str:
        """현재 맵에서 가장 많이 남아있는 색 선택함.

        Returns:
            str: 가장 많이 등장한 색을 반환
        """
        color_count:dict[str,int]={}

        for b in self.grid.bubble_list:
            if b.color in COLORS:
                color_count[b.color]=color_count.get(b.color,0)+1

        # 맵 거의 비어있으면 그냥 랜덤 색
        if not color_count:
            return random.choice(list(COLORS.keys()))
        # 가장 많이 등장한 색 반환함.
        best=max(color_count,key=color_count.get)
        return best

    def use_item_rainbow(self)->None:
        """현재 버블을 최적의 색으로 변경함.
        """
        if self.item_rainbow_count<=0:
            print("No RAINBOW items left.")
            return
        if self.current_bubble is None:
            print("Cannot use RAINBOW: current bubble is missing.")
            return

        # 변환 전 색상 저장
        original_color = self.current_bubble.color
        
        # 최적 색상으로 변환
        best_color = self.best_color_for_rainbow()
        self.current_bubble.color = best_color

        self.item_rainbow_count -= 1
        
        # 변환 전후 색상 출력
        print(f"🌈 RAINBOW: {original_color} → {best_color}")
        print(f"RAINBOW used. Remaining: {self.item_rainbow_count}")

    def draw(self)->None:
        if self.background_image:
            self.screen.blit(self.background_image,(0,0))
        else:
            self.screen.fill((10,20,30))

        pygame.draw.rect(self.screen,(0,100,200),self.game_rect)

        pygame.draw.line(self.screen,(0,255,3),
                         (self.game_rect.left,self.game_over_line),
                         (self.game_rect.right,self.game_over_line),10)

        self.grid.draw(self.screen)
        self.cannon.draw(self.screen)
        if self.current_bubble:
            self.current_bubble.draw(self.screen)

        if self.char_left:
            char_left_x = self.game_rect.left - int(419*SCALE)
            char_left_y = SCREEN_HEIGHT - int(617*SCALE)
            self.screen.blit(self.char_left,(char_left_x, char_left_y))
        if self.char_right:
            char_right_x = self.game_rect.right + int(80*SCALE)
            char_right_y = SCREEN_HEIGHT - int(617*SCALE)
            self.screen.blit(self.char_right,(char_right_x, char_right_y))
        if self.logo:
            logo_x = SCREEN_WIDTH - int(198*SCALE)
            logo_y = int(18*SCALE)
            self.screen.blit(self.logo,(logo_x, logo_y))

        if self.next_bubble:
            # NEXT 버블 위치를 config.py 설정값 사용 (스케일 적용)
            next_x = int(NEXT_BUBBLE_X * SCALE)
            next_y_offset = int(NEXT_BUBBLE_Y_OFFSET * SCALE) if NEXT_BUBBLE_Y_OFFSET < 0 else int(NEXT_BUBBLE_Y_OFFSET * SCALE)
            next_y = SCREEN_HEIGHT + next_y_offset if NEXT_BUBBLE_Y_OFFSET < 0 else next_y_offset

            try:
                font_size = int(40 * SCALE)
                font = pygame.font.Font(ASSET_PATHS['font'], font_size) if ASSET_PATHS['font'] else pygame.font.Font(None, font_size)
            except:
                font = pygame.font.Font(None, int(40 * SCALE))
            next_txt = font.render("NEXT", True, (0,0,0))
            next_txt_offset_y = int(70 * SCALE)
            next_txt_rect = next_txt.get_rect(center=(next_x, next_y - next_txt_offset_y))
            self.screen.blit(next_txt, next_txt_rect)

            original_x, original_y = self.next_bubble.x, self.next_bubble.y
            self.next_bubble.x, self.next_bubble.y = next_x, next_y
            self.next_bubble.draw(self.screen)
            self.next_bubble.x, self.next_bubble.y = original_x, original_y

        self.score_ui.draw(self.screen,self.current_stage+1)

        self.draw_item_buttons(self.screen)
            # 아이템 버튼 그리기.

        pygame.display.flip()

    def show_stage_clear(self)->None:
        overlay=pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0,0,0))
        self.screen.blit(overlay,(0,0))

        font=pygame.font.Font(ASSET_PATHS['font'],120)
        text=font.render('CLEAR!',True,(100,255,100))
        rect=text.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2))
        self.screen.blit(text,rect)

        small_font=pygame.font.Font(ASSET_PATHS['font'],50)
        info=small_font.render(
            f'Stage {self.current_stage+1} Complete.',
            True,
            (200,200,200)
        )
        info_rect=info.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2+80))
        self.screen.blit(info,info_rect)

        pygame.display.flip()
        pygame.time.delay(1000)

    def run(self)->None:
        while self.running:
            self.clock.tick(FPS)
            self.update()
            self.draw()

        pygame.mixer.music.stop()

        self.screen.fill((0,0,0))
        font=pygame.font.Font(ASSET_PATHS['font'],100)

        next_csv_path=f'assets/map_data/stage{self.current_stage+1}.csv'
        if not os.path.exists(next_csv_path):
            msg="you win."
        else:
            msg="game over."

        txt=font.render(msg,True,(255,255,255))
        rect=txt.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2))
        self.screen.blit(txt,rect)

        pygame.display.flip()
        pygame.time.delay(END_SCREEN_DELAY)
