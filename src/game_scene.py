# 게임 로직으로 전환하기 위한 씬입니다.
import pygame
# from menu_scene import MenuScene

class GameScene:
    def __init__(self,manager):
        self.manager=manager
        self.running=True

    def handle_event(self,event):
        """게임 씬 내 이벤트 처리"""
        if event.type==pygame.QUIT:
            self.running=False

        if event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE:
                self.running=False

    def update(self):
        """씬 이름만 넘겨서 매니저가 팩토리로부터 씬 만듦."""
        if not self.running:
            # self.manager.change(MenuScene(self.manager))
            self.manager.change('menu')

    # FIXME: 게임 씬 배경을 일단 녹색으로 설정함.
    def draw(self,screen):
        """게임 로직에 따른 그리기 작업 수행함."""
        # FIXME: 일단 초록색 배경으로
        screen.fill((0,255,0))
        # if not self.running:
        #     from menu_scene import MenuScene
        #         # [수정: lazy import 사용]
        #     self.manager.change(MenuScene(self.manager))
        # if not self.running:
        #     self.manager.change(MenuScene(self.manager))
                # 게임 종료 시 메뉴로 돌아감.
