class SceneManager:
    def __init__(self,scene_factory):
        self.scene_factory=scene_factory
        self.current_scene=None

    def run(self,initial_scene_name):
        scene_name=initial_scene_name
        while scene_name is not None:
            self.current_scene=self.scene_factory(scene_name,self)
            if not hasattr(self.current_scene,'run'):
                raise AttributeError(f'scene {scene_name} has no run()')
            scene_name=self.current_scene.run()
        # None 리턴되면 전체 게임 종료
