import pygame


class Projectile(pygame.sprite.Sprite):
    """Projétil padrão do jogador.

    A classe foi extraída para o módulo de combate para reduzir acoplamento com
    o arquivo principal. Ela mantém a interface usada no gameplay.
    """

    def __init__(self, pos, vel, dmg, frames, pierce=0, ricochet=0, screen_size_getter=lambda: (1920, 1080)):
        super().__init__()
        self.anim_frames = frames
        self.frame_idx = 0
        self.anim_timer = 0.0
        self.image = self.anim_frames[0]
        self.rect = self.image.get_rect()
        self.hitbox = self.rect.inflate(-max(4, self.rect.width // 6), -max(4, self.rect.height // 6))
        self.pos = pygame.Vector2(pos.x, pos.y)
        self.vel = vel
        self.dmg = dmg
        self.pierce = pierce
        self.hit_enemies = []
        self.ricochet = ricochet
        self.is_melee = False
        self._screen_size_getter = screen_size_getter

    def update(self, dt, cam):
        self.pos += self.vel * dt
        self.anim_timer += dt
        if self.anim_timer > 0.05:
            self.anim_timer = 0.0
            self.frame_idx = (self.frame_idx + 1) % len(self.anim_frames)
            self.image = self.anim_frames[self.frame_idx]
        self.rect.center = self.pos + cam
        self.hitbox = self.rect.inflate(-max(4, self.rect.width // 6), -max(4, self.rect.height // 6))
        self.hitbox.center = self.rect.center

        screen_w, screen_h = self._screen_size_getter()
        if not pygame.Rect(-1000, -1000, screen_w + 2000, screen_h + 2000).collidepoint(self.rect.center):
            self.kill()


class MeleeSlash(pygame.sprite.Sprite):
    """Golpe melee animado que acompanha a posição do jogador."""

    def __init__(self, player, target_dir, dmg, frames):
        super().__init__()
        self.anim_frames = frames
        self.frame_idx = 0
        self.anim_timer = 0.0
        self.player = player
        self.target_dir = target_dir.normalize() if target_dir.length() > 0 else pygame.Vector2(1, 0)
        self.distance = 90
        self.is_melee = True

        shoot_angle = pygame.Vector2(1, 0).angle_to(self.target_dir)
        self.anim_frames = [pygame.transform.rotate(frame, -shoot_angle) for frame in frames]
        self.image = self.anim_frames[0]
        self.rect = self.image.get_rect()
        self.pos = self.player.pos + (self.target_dir * self.distance)
        self.dmg = dmg
        self.hit_enemies = []

    def update(self, dt, cam):
        self.anim_timer += dt
        if self.anim_timer > 0.04:
            self.anim_timer = 0.0
            self.frame_idx += 1
            if self.frame_idx >= len(self.anim_frames):
                self.kill()
                return
            self.image = self.anim_frames[self.frame_idx]

        self.pos = self.player.pos + (self.target_dir * self.distance)
        self.rect.center = self.pos + cam


def projectile_enemy_collision(projectile, enemy):
    """Teste de colisão entre projétil e inimigo usando hitbox quando existir."""

    p_rect = getattr(projectile, "hitbox", projectile.rect)
    return p_rect.colliderect(enemy.rect)
