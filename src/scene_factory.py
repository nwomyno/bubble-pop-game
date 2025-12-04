from menu_scene import MenuScene
from game_scene_wrapper import GameSceneWrapper
from editor_scene import EditorScene

def scene_factory(name,manager):
    if name=='menu':
        return MenuScene(manager)
    if name=='game':
        return GameSceneWrapper(manager)
    if name=='editor':
        return EditorScene(manager)
    raise ValueError(f'unknown scene: {name}')
