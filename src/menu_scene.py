import pygame
import os
from config import SCREEN_WIDTH, SCREEN_HEIGHT, SCALE

class MenuScene:
    def __init__(self, manager):
        self.manager = manager
        self.idx = 0
        
        # 이미지 경로 설정
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'images')
        
        # 배경 이미지 로드 및 스케일 조정
        background_img = pygame.image.load(os.path.join(base_path, 'menu_background.png'))
        self.background = pygame.transform.scale(background_img, (int(SCREEN_WIDTH), int(SCREEN_HEIGHT)))
        
        # 버튼 이미지 로드 및 스케일 조정
        button_files = ['menu_start.png', 'menu_map_editor.png', 'menu_exit.png']
        self.button_images = []
        for btn_file in button_files:
            img = pygame.image.load(os.path.join(base_path, btn_file))
            # 버튼 이미지를 SCALE에 맞게 조정
            scaled_img = pygame.transform.scale(img, (int(img.get_width() * SCALE), int(img.get_height() * SCALE)))
            self.button_images.append(scaled_img)
        
        # 버튼 위치 설정 (스케일 기반)
        base_button_start_y = 600  # 기본 해상도 기준 버튼 시작 Y 위치
        base_button_spacing = 120  # 기본 해상도 기준 버튼 간격
        
        self.button_rects = []
        for i in range(len(self.button_images)):
            img = self.button_images[i]
            y_pos = int(base_button_start_y * SCALE + i * base_button_spacing * SCALE)
            rect = img.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
            self.button_rects.append(rect)
        
        # 테두리 두께도 스케일 기반으로 설정
        self.border_thickness = max(2, int(3 * SCALE))

    def run(self):
        screen = pygame.display.get_surface()
        clock = pygame.time.Clock()
        running = True

        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return None
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_UP, pygame.K_w):
                        self.idx = (self.idx - 1) % len(self.button_images)
                    elif e.key in (pygame.K_DOWN, pygame.K_s):
                        self.idx = (self.idx + 1) % len(self.button_images)
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.idx == 0:
                            return 'game'
                        elif self.idx == 1:
                            return 'editor'
                        else:
                            return None

            # 배경 이미지 그리기
            screen.blit(self.background, (0, 0))

            # 버튼 이미지 그리기
            for i in range(len(self.button_images)):
                img = self.button_images[i]
                rect = self.button_rects[i]
                
                # 버튼 이미지 그리기
                screen.blit(img, rect)
                
                # 선택된 버튼에 테두리 그리기 (스케일 기반 두께)
                if i == self.idx:
                    pygame.draw.rect(screen, (255, 255, 255), rect, self.border_thickness)

            pygame.display.flip()
            clock.tick(60)

        return None
