from game import Game

class GameSceneWrapper:
    def __init__(self,manager):
        self.manager=manager

    def run(self):
        # Game 내부에서 자체 루프 돌고 끝나면 run() 리턴됨
        g=Game()
        g.run()

        # 게임 끝나고 나면 다시 메뉴로 돌아감
        return 'menu'
