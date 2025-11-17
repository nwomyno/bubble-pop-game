# 게임 로직으로 전환하기 위한 씬입니다.
import pygame

class GameScene:
    def __init__(self,manager):
        self.manager=manager

    def handle_event(self,event):
        """게임 씬 내 이벤트 처리"""
        pass

    def update(self):
        """게임 상태 업데이트함."""
        pass

    # FIXME: 게임 씬 배경을 일단 녹색으로 설정함.
    def draw(self,screen):
        """게임 로직에 따른 그리기 작업 수행함."""
        screen.fill((0,255,0))
