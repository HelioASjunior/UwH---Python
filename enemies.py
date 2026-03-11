import math
import random

import pygame


class EnemyProjectile(pygame.sprite.Sprite):
    """Projétil de inimigo modularizado."""

    def __init__(self, pos, vel, dmg, loader, img_name):
        super().__init__()
        base_frames = loader.load_animation(img_name, 4, (36, 36), fallback_colors=((255, 120, 0), (200, 50, 0)))
        shoot_angle = math.degrees(math.atan2(-vel.y, vel.x))
        self.anim_frames = [pygame.transform.rotate(frame, shoot_angle) for frame in base_frames]
        self.frame_idx = 0
        self.anim_timer = 0
        self.image = self.anim_frames[0]
        self.rect = self.image.get_rect()
        self.pos = pygame.Vector2(pos.x, pos.y)
        self.vel = vel
        self.dmg = dmg

    def update(self, dt, cam, screen_w, screen_h):
        self.pos += self.vel * dt
        self.anim_timer += dt
        if self.anim_timer > 0.05:
            self.anim_timer = 0
            self.frame_idx = (self.frame_idx + 1) % len(self.anim_frames)
            self.image = self.anim_frames[self.frame_idx]
        self.rect.center = self.pos + cam
        world_rect = pygame.Rect(-1000, -1000, screen_w + 2000, screen_h + 2000)
        if not world_rect.collidepoint(self.rect.center):
            self.kill()


class Enemy(pygame.sprite.Sprite):
    """Classe de inimigo modularizada.

    Recebe fábricas por parâmetro na atualização para evitar acoplamento direto
    com o arquivo principal.
    """

    def __init__(self, kind, pos, loader, diff_mults, screen_size_getter, time_scale=1.0, boss_tier=1, is_elite=False, boss_max_hp=500):
        super().__init__()
        self.kind = kind
        self.is_elite = is_elite
        self.screen_size_getter = screen_size_getter

        self.knockback = pygame.Vector2(0, 0)
        self.flash_timer = 0.0
        self.frozen_timer = 0.0

        if kind == "boss":
            color = ((50, 0, 0), (0, 0, 0))
            size = (250, 250)
            frames = 4
        elif kind == "shooter":
            color = ((200, 50, 200), (120, 0, 120))
            size = (110, 95)
            frames = 11
        elif kind == "tank":
            color = ((50, 200, 50), (0, 120, 0))
            size = (100, 90)
            frames = 11
        elif kind == "elite":
            color = ((255, 200, 0), (150, 100, 0))
            size = (100, 90)
            frames = 11
        elif kind == "slime":
            color = ((20, 20, 20), (50, 100, 50))
            size = (90, 80)
            frames = 10
        elif kind == "robot":
            color = ((100, 100, 150), (50, 50, 100))
            size = (100, 100)
            frames = 4
        else:
            color = ((255, 100, 100), (150, 0, 0))
            size = (100, 100)
            frames = 11

        self.anim_frames = loader.load_animation(kind, frames, size, fallback_colors=color)
        self.flipped_frames = [pygame.transform.flip(frame, True, False) for frame in self.anim_frames]

        self.white_frames = []
        for frame in self.anim_frames:
            mask = pygame.mask.from_surface(frame)
            white_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
            self.white_frames.append(white_surf)
        self.flipped_white_frames = [pygame.transform.flip(frame, True, False) for frame in self.white_frames]

        self.frozen_frames = []
        for frame in self.anim_frames:
            mask = pygame.mask.from_surface(frame)
            blue_surf = mask.to_surface(setcolor=(0, 255, 255, 150), unsetcolor=(0, 0, 0, 0))
            combined = frame.copy()
            combined.blit(blue_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            self.frozen_frames.append(combined)
        self.flipped_frozen_frames = [pygame.transform.flip(frame, True, False) for frame in self.frozen_frames]

        self.frame_idx = 0
        self.anim_timer = 0.0
        self.facing_right = True
        self.shot_timer = 0.0
        self.shot_cooldown = 3.0
        self.puddle_timer = 0.0

        self.image = self.anim_frames[0]
        self.rect = self.image.get_rect()
        self.pos = pos

        stats = {
            "runner": (2, 150),
            "tank": (10, 65),
            "elite": (60, 85),
            "shooter": (3, 90),
            "boss": (boss_max_hp, 95),
            "slime": (5, 110),
            "robot": (8, 130),
        }
        base_hp, base_spd = stats[kind]

        if kind == "robot":
            self.shot_cooldown = 1.0

        if kind == "boss":
            self.hp = base_hp * diff_mults["hp_mult"] * time_scale * boss_tier
        else:
            self.hp = base_hp * diff_mults["hp_mult"] * time_scale

        self.speed = base_spd * diff_mults["spd_mult"] * min(1.5, time_scale)
        self.max_hp = self.hp

    def update(self, dt, p_pos, cam, obstacles, enemy_projectiles, puddles, loader, selected_pact, enemy_projectile_cls, puddle_cls, shooter_proj_image):
        self.pos += self.knockback
        self.knockback *= 0.85

        if self.flash_timer > 0:
            self.flash_timer -= dt

        if self.frozen_timer > 0:
            self.frozen_timer -= dt
            current_set = self.frozen_frames if self.facing_right else self.flipped_frozen_frames
            self.image = current_set[self.frame_idx]
            self.rect.center = self.pos + cam
            return

        direction = (p_pos - self.pos)
        dist = direction.length()
        can_move = self.knockback.length() < 3.0

        if dist > 0 and can_move:
            is_ranged_unit = self.kind in ["shooter", "robot"]
            stop_dist = 450 if self.kind == "shooter" else 300
            if is_ranged_unit and dist < stop_dist:
                move = pygame.Vector2(0, 0)
            else:
                move_speed = self.speed
                if selected_pact == "VELOCIDADE":
                    move_speed *= 1.5
                if self.kind == "boss":
                    if self.hp < self.max_hp * 0.25:
                        move_speed *= 2.0
                    elif self.hp < self.max_hp * 0.5:
                        move_speed *= 1.5
                move = (direction / dist) * move_speed * dt

            if direction.x > 0:
                self.facing_right = True
            elif direction.x < 0:
                self.facing_right = False

            if move.length_squared() > 0:
                self.pos += move
                if self.kind != "boss":
                    for obs in obstacles:
                        if obs.hitbox.collidepoint(self.pos):
                            self.pos -= move

            anim_speed = 0.15 if self.kind == "boss" else 0.1
            self.anim_timer += dt
            if self.anim_timer > anim_speed:
                self.anim_timer = 0
                self.frame_idx = (self.frame_idx + 1) % len(self.anim_frames)

        if self.kind in ["shooter", "robot", "boss"]:
            self.shot_timer += dt
            current_cooldown = self.shot_cooldown
            if self.kind == "boss":
                if self.hp < self.max_hp * 0.25:
                    current_cooldown *= 0.4
                elif self.hp < self.max_hp * 0.5:
                    current_cooldown *= 0.7

            if self.shot_timer >= current_cooldown:
                self.shot_timer = 0.0
                if self.kind == "boss":
                    num_shots = 8
                    if self.hp < self.max_hp * 0.25:
                        num_shots = 16
                    elif self.hp < self.max_hp * 0.5:
                        num_shots = 12
                    for i in range(num_shots):
                        angle = (360 / num_shots) * i
                        vel = pygame.Vector2(1, 0).rotate(angle) * 350.0
                        enemy_projectiles.add(enemy_projectile_cls(self.pos, vel, 1.0, loader, shooter_proj_image))
                else:
                    range_limit = 500 if self.kind == "shooter" else 450
                    if 0 < dist < range_limit:
                        speed_proj = 300.0 if self.kind == "shooter" else 150.0
                        vel = (direction / dist) * speed_proj
                        enemy_projectiles.add(enemy_projectile_cls(self.pos, vel, 0.5, loader, shooter_proj_image))

        if self.kind == "slime":
            self.puddle_timer += dt
            if self.puddle_timer >= 2.5:
                self.puddle_timer = 0.0
                puddles.add(puddle_cls(self.pos, loader))

        if self.flash_timer > 0:
            current_set = self.white_frames if self.facing_right else self.flipped_white_frames
        else:
            current_set = self.anim_frames if self.facing_right else self.flipped_frames

        self.image = current_set[self.frame_idx]

        if self.is_elite:
            aura_surf = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            pygame.draw.ellipse(aura_surf, (255, 215, 0, 100), aura_surf.get_rect(), 3)
            self.image = self.image.copy()
            self.image.blit(aura_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        self.rect.center = self.pos + cam
