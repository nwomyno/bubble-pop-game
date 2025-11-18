import sys
import pygame

from config import SCREEN_WIDTH,SCREEN_HEIGHT
from scene_manager import SceneManager
from scene_factory import scene_factory

def main():
    pygame.init()
    pygame.mixer.init()

    pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))

    manager=SceneManager(scene_factory)
    manager.run('menu')

    pygame.quit()
    sys.exit()

if __name__=='__main__':
    main()
