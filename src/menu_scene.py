import pygame
from config import SCREEN_WIDTH,SCREEN_HEIGHT

class MenuScene:
    def __init__(self,manager):
        self.manager=manager
        self.font=pygame.font.Font(None,80)
        self.small=pygame.font.Font(None,40)
        self.opts=['Start Game','Map Editor','Quit']
        self.idx=0

    def run(self):
        screen=pygame.display.get_surface()
        clock=pygame.time.Clock()
        running=True

        while running:
            for e in pygame.event.get():
                if e.type==pygame.QUIT:
                    return None
                if e.type==pygame.KEYDOWN:
                    if e.key in (pygame.K_UP,pygame.K_w):
                        self.idx=(self.idx-1)%len(self.opts)
                    elif e.key in (pygame.K_DOWN,pygame.K_s):
                        self.idx=(self.idx+1)%len(self.opts)
                    elif e.key in (pygame.K_RETURN,pygame.K_SPACE):
                        if self.idx==0:
                            return 'game'
                        elif self.idx==1:
                            return 'editor'
                        else:
                            return None

            screen.fill((25,25,25))

            title=self.font.render('BUBBLE POP',True,(255,255,255))
            t_rect=title.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2-100))
            screen.blit(title,t_rect)

            for i,text in enumerate(self.opts):
                col=(255,255,255) if i==self.idx else (150,150,150)
                surf=self.small.render(text,True,col)
                r=surf.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2+40+i*50))
                screen.blit(surf,r)

            pygame.display.flip()
            clock.tick(60)

        return None
