class SceneManager:
    def __init__(self,start_scene):
        self.current_scene = start_scene

    def change(self,new_scene):
        """씬 전환"""
        self.current_scene=new_scene

    def handle_event(self,event):
        """현재 씬 이벤트 처리"""
        self.current_scene.handle_event(event)

    def update(self):
        """현재 씬 업데이트"""
        self.current_scene.update()

    def draw(self,screen):
        """현재 씬 그리기."""
        self.current_scene.draw(screen)
