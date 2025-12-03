from enum import Enum

class BubbleColor(Enum):
    """버블 색 정의"""

    RED='R'
    YELLOW='Y'
    BLUE='B'
    GREEN='G'

class GameState(Enum):
    """게임 상태 정의"""
    MENU='menu'
    PLAYING='playing'
    PAUSED='paused'
    GAME_OVER='game_over'

class Itemtype(Enum):
    """아이템 종류 정의"""
    # BOMB='bomb'
        # 나중에 추가할 아이템 종류?
    NONE='none'
    SWAP='swap'
        # 버블 스왑
    RAISE='raise'
        # 벽 한 줄 올리기
    RAINBOW='rainbow'
        # 무지개 버블
