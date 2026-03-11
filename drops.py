import math

import pygame


class Drop(pygame.sprite.Sprite):
    """Entidade de drop modularizada para reduzir o tamanho do arquivo principal."""

    def __init__(self, pos, kind, loader):
        super().__init__()
        self.kind = kind
        self.pos = pygame.Vector2(pos)

        size = (55, 55)
        if kind == "chicken":
            color = ((255, 100, 100), (200, 50, 50))
            img_name = "item_chicken"
        elif kind == "magnet":
            color = ((100, 100, 255), (50, 50, 200))
            img_name = "item_magnet"
        elif kind == "chest":
            color = ((255, 215, 0), (200, 150, 0))
            img_name = "item_chest"
            size = (70, 70)
        elif kind == "coin":
            color = ((255, 215, 0), (255, 255, 100))
            img_name = "item_coin"
            size = (30, 30)
        else:
            color = ((50, 50, 50), (20, 20, 20))
            img_name = "item_bomb"

        self.image = loader.load_image(img_name, size, fallback_colors=color)
        self.rect = self.image.get_rect(center=pos)
        self.float_timer = 0.0

    def update(self, dt, cam):
        self.float_timer += dt * 5
        offset = math.sin(self.float_timer) * 5
        self.rect.center = (self.pos.x + cam.x, self.pos.y + cam.y + offset)
