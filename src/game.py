import math
import random
import sys
import csv
import os
from typing import List,Set,Tuple,Optional

import pygame

from config import (
    SCREEN_WIDTH,SCREEN_HEIGHT,FPS,CELL_SIZE,BUBBLE_RADIUS,BUBBLE_SPEED,
    LAUNCH_COOLDOWN,WALL_DROP_PIXELS,MAP_ROWS,MAP_COLS,
    NEXT_BUBBLE_X,NEXT_BUBBLE_Y_OFFSET
)
from game_settings import (
    END_SCREEN_DELAY,POP_SOUND_VOLUME,TAP_SOUND_VOLUME
)
from asset_paths import ASSET_PATHS
from constants import BubbleColor,GameState
from color_settings import (COLORS,
                            COLOR_MAP)

from pathlib import Path
sys.path.append(str(Path(__file__).parent))

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
        print(f"경고: {csv_path} 파일을 찾을 수 없습니다. 기본 맵을 사용합니다.")
        return [['.' for _ in range(MAP_COLS)] for _ in range(MAP_ROWS)]

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

    def load_from_stage(self,stage_map:List[List[str]])->None:
        self.map=[row[:] for row in stage_map]
        self.bubble_list=[]
        for r in range(self.rows):
            if r>=len(self.map):
                break
            for c in range(self.cols):
                if c<len(self.map[r]):
                    ch=self.map[r][c]
                else:
                    ch='.'
                if ch in COLORS:
                    x,y=self.get_cell_center(r,c)
                    b=Bubble(x,y,ch)
                    b.is_attached=True
                    b.set_grid_index(r,c)
                    self.bubble_list.append(b)

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

    def drop_wall(self)->None:
        self.wall_offset+=WALL_DROP_PIXELS
        for b in self.bubble_list:
            cx,cy=self.get_cell_center(b.row_idx,b.col_idx)
            b.x,b.y=cx,cy

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
        self.grid_x_offset=((SCREEN_WIDTH-map_pixel_width)//2)+25
        self.grid_y_offset=30

        padding=10
        game_area_w=map_pixel_width+(padding*2)
        game_area_h=SCREEN_HEIGHT-self.grid_y_offset
        game_area_x=(SCREEN_WIDTH-game_area_w)//2
        game_area_y=self.grid_y_offset-padding
        self.game_rect=pygame.Rect(game_area_x,game_area_y,game_area_w,game_area_h)

        self.grid:HexGrid=HexGrid(MAP_ROWS,MAP_COLS,CELL_SIZE,
                                  0,
                                  self.grid_x_offset,self.grid_y_offset)

        cannon_x=self.game_rect.centerx
        cannon_y=self.game_rect.bottom-170
        self.cannon:Cannon=Cannon(cannon_x,cannon_y)

        self.game_over_line=self.cannon.y-CELL_SIZE*0.5
        self.score_ui:ScoreDisplay=ScoreDisplay()

        try:
            self.background_image=pygame.image.load(ASSET_PATHS['background']).convert()
            self.background_image=pygame.transform.scale(self.background_image,(SCREEN_WIDTH,SCREEN_HEIGHT))

            self.char_left=pygame.image.load(ASSET_PATHS['char_left']).convert_alpha()
            self.char_right=pygame.image.load(ASSET_PATHS['char_right']).convert_alpha()
            self.logo=pygame.image.load(ASSET_PATHS['logo']).convert_alpha()

            self.char_left=pygame.transform.smoothscale(self.char_left,(313,546))
            self.char_right=pygame.transform.smoothscale(self.char_right,(308,555))
            self.logo=pygame.transform.smoothscale(self.logo,(176,176))

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
            self.screen.blit(self.char_left,(self.game_rect.left-419,SCREEN_HEIGHT-617))
        if self.char_right:
            self.screen.blit(self.char_right,(self.game_rect.right+80,SCREEN_HEIGHT-617))
        if self.logo:
            self.screen.blit(self.logo,(SCREEN_WIDTH-198,18))

        if self.next_bubble:
            next_x=NEXT_BUBBLE_X
            next_y=SCREEN_HEIGHT+NEXT_BUBBLE_Y_OFFSET if NEXT_BUBBLE_Y_OFFSET<0 else NEXT_BUBBLE_Y_OFFSET

            try:
                font=pygame.font.Font(ASSET_PATHS['font'],40) if ASSET_PATHS['font'] else pygame.font.Font(None,40)
            except:
                font=pygame.font.Font(None,40)
            next_txt=font.render("NEXT",True,(0,0,0))
            next_txt_rect=next_txt.get_rect(center=(next_x,next_y-70))
            self.screen.blit(next_txt,next_txt_rect)

            original_x,original_y=self.next_bubble.x,self.next_bubble.y
            self.next_bubble.x,self.next_bubble.y=next_x,next_y
            self.next_bubble.draw(self.screen)
            self.next_bubble.x,self.next_bubble.y=original_x,original_y

        self.score_ui.draw(self.screen,self.current_stage+1)
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
