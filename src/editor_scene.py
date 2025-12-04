import pygame
from map_editor import MapEditor

class EditorScene:
    """Map Editor를 Scene으로 래핑하는 클래스"""
    def __init__(self, manager):
        self.manager = manager
        self.editor = None
    
    def run(self):
        """Map Editor 실행"""
        # MapEditor 인스턴스 생성 (이미 pygame.init()은 main.py에서 완료됨)
        self.editor = MapEditor()
        
        # 에디터 실행 (ESC 키로 종료 가능)
        self.editor.run()
        
        # 에디터가 종료되면 메뉴로 돌아감
        return 'menu'
