import pygame

class Obstacle:
    """안 움직이고 DFS에도 안 들어감.
    """
    def __init__(self,x,y,radius,row_idx,col_idx):
        self.x = x
        self.y = y
        self.radius = radius
        self.row_idx = row_idx
        self.col_idx = col_idx
        self.is_static = True
            # 장애물 고정 여부

    # 색은 회색 계열로 설정 (임시)
    def draw(self, screen):
        """장애물 그리기

        Args:
            screen (_type_): _description_
        """
        pygame.draw.circle(screen,(90,90,90),(int(self.x),int(self.y)),self.radius)
        pygame.draw.circle(screen,(160,160,160),(int(self.x),int(self.y)),self.radius,4)
