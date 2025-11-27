import sys
import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT
from scene_manager import SceneManager
from scene_factory import scene_factory


def main() -> None:
    """프로그램 엔트리포인트: 메뉴 → 게임 씬으로 진입."""
    pygame.init()
    pygame.mixer.init()

    # 전역 디스플레이 생성 (모든 Scene은 이 surface를 공유)
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    manager = SceneManager(scene_factory)
    # 첫 씬은 메뉴부터 시작
    manager.run("menu")

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
