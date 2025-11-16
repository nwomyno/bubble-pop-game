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
