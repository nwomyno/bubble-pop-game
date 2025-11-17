import pygame
from scene_manager import SceneManager
from game_scene import GameScene

class MenuScene:
    def __init__(self,manager):
        self.manager=manager
        # FIXME: 폰트 임시 설정
        self.font=pygame.font.SysFont('Arial',48)
        self.options=['Start Game','Settings','Quit']
            # 메뉴 항목
        self.selected_index=0
            # 리스트 안에서 현재 선택된 인덱스

    def handle_event(self,event):
        if event.type==pygame.KEYDOWN:
            # 위로 이동하면
            if event.key==pygame.K_UP:
                self.selected_index=(self.selected_index-1)%len(self.options)
            # 아래로 이동하면
            elif event.key==pygame.K_DOWN:
                self.selected_index=(self.selected_index+1)%len(self.options)
            # 선택하면
            elif event.key==pygame.K_RETURN:
                # Start Game 선택 시
                if self.selected_index==0:
                    self.manager.change(GameScene(self.manager))
                # Exit 선택 시
                elif self.selected_index==2:
                    pygame.quit()
                    exit()

    def draw(self,screen):
        # FIXME: 배경 색상 임시 설정
        screen.fill((30,30,30))
        for index, option in enumerate(self.options):
            # FIXME: RGB 값 임시 설정
            color=(255,255,255)if index==self.selected_index else (200,200,200)

            text=self.font.render(option,True,color)
                # 렌더링
            # FIXME: 위치 조정
            text_rectangle=text.get_rect(center=(400,250+index*50))

            screen.blit(text,text_rectangle)
