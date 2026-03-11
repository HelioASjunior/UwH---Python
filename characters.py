"""Sistema de personagens do UnderWorld Hero.

Este módulo existe para tirar a responsabilidade de personagens de dentro do
arquivo principal do jogo. A ideia é simples:

1. O arquivo principal continua sendo o dono do loop do jogo, dos sprites
   globais, dos assets e das regras gerais da run.
2. Cada personagem passa a encapsular sua própria identidade: ataque básico,
   dash, ultimate, nomes exibidos na HUD e efeitos especiais.
3. O acoplamento com o restante do projeto é feito por injeção de dependências,
   evitando import circular com jogo_final.py.

Com essa separação, editar um personagem fica muito mais barato: quase sempre a
mudança ficará concentrada neste arquivo, sem exigir vários if/else no loop
principal.
"""

import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pygame


@dataclass
class CharacterDependencies:
    """Agrupa tudo o que o módulo de personagens precisa receber do jogo.

    Em vez de importar classes e funções do arquivo principal, recebemos essas
    referências prontas. Isso mantém o módulo independente e reduz o risco de
    dependências circulares.
    """

    char_data_map: dict
    control_reader: object
    particle_cls: object
    damage_text_cls: object
    projectile_cls: object
    melee_slash_cls: object
    gem_cls: object
    dash_speed: float
    dash_duration: float
    dash_cooldown: float
    ultimate_max_charge: int
    screen_size_getter: object


@dataclass
class CharacterCombatContext:
    """Carrega o estado dinâmico usado pelos personagens em combate.

    Este contexto é remontado pelo arquivo principal sempre que necessário,
    porque os valores mudam o tempo todo durante a run: upgrades, grupos de
    sprites, dano atual, speed de projétil e assim por diante.
    """

    enemies: object = None
    projectiles: object = None
    particles: object = None
    damage_texts: object = None
    gems: object = None
    projectile_frames_raw: object = None
    slash_frames_raw: object = None
    loader: object = None
    projectile_speed: float = 0.0
    projectile_damage: float = 0.0
    projectile_count: int = 1
    fury_multiplier: float = 1.0
    bazooka_active: bool = False


@dataclass
class CharacterActionFeedback:
    """Resposta padronizada para ações de personagem.

    O loop principal usa esse retorno para tocar sons, alimentar o log lateral
    e disparar pequenos efeitos de interface sem precisar conhecer os detalhes
    de implementação da habilidade.
    """

    activated: bool = False
    sound_name: str = ""
    log_text: str = ""
    log_color: tuple = (220, 220, 220)
    kills_gained: int = 0


class Player(ABC, pygame.sprite.Sprite):
    """Classe base abstrata com o comportamento comum a todo personagem.

    Esta classe concentra apenas o que realmente é compartilhado:

    - carregamento de animação
    - movimentação e colisão
    - timers de dash
    - carga/tempo de ultimate
    - hooks para as subclasses personalizarem ataque e skills

    O objetivo não é ter uma classe “genérica demais”, mas sim um esqueleto bem
    estável sobre o qual cada herói pode construir sua própria identidade.
    """

    def __init__(self, loader, char_id, dependencies):
        super().__init__()
        self.deps = dependencies
        self.char_id = char_id
        self.data = dependencies.char_data_map[char_id]
        self.name = self.data.get("name", f"CHAR_{char_id}")

        # Cada personagem pode informar seu próprio tamanho e quantidade de
        # frames diretamente no CHAR_DATA, sem hardcode espalhado no jogo.
        char_size = self.data.get("size", (180, 180))
        anim_frames_count = self.data.get("anim_frames", 11)
        self.anim_frames = loader.load_animation(f"char{char_id}", anim_frames_count, char_size)
        self.flipped_frames = [pygame.transform.flip(frame, True, False) for frame in self.anim_frames]

        self.frame_idx = 0
        self.anim_timer = 0.0
        self.facing_right = True
        self.image = self.anim_frames[0]
        self.rect = self.image.get_rect()
        self.pos = pygame.Vector2(0, 0)
        self.vel = pygame.Vector2(0, 0)

        # Os atributos base também vêm do CHAR_DATA. Isso facilita balancear um
        # personagem sem tocar na lógica do loop principal.
        self.base_hp = self.data.get("hp", 5)
        self.base_speed = self.data.get("speed", 280)
        self.base_damage = self.data.get("damage", 2)
        self.dash_speed = self.data.get("dash_speed", dependencies.dash_speed)
        self.dash_duration = self.data.get("dash_duration", dependencies.dash_duration)
        self.dash_cooldown = self.data.get("dash_cooldown", dependencies.dash_cooldown)

        self.dash_active = False
        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0

        self.ult_charge = 0
        self.ult_max = dependencies.ultimate_max_charge
        self.ult_active_timer = 0.0
        self.ult_active = False

        self.hp = self.base_hp
        self.iframes = 0.0

    def get_attack_name(self):
        """Nome curto do ataque básico exibido na HUD."""
        return "Disparo Rúnico"

    def get_dash_name(self):
        """Nome curto do dash exibido na HUD e no feed lateral."""
        return "Deslocamento"

    def get_ultimate_name(self):
        """Nome curto do ultimate exibido na HUD e no feed lateral."""
        return "Poder Supremo"

    def get_skill_cards(self):
        """Retorna as três skills principais mostradas na interface.

        O formato foi mantido simples para o arquivo principal só se preocupar
        com renderização.
        """

        return [
            ("Ataque", self.get_attack_name()),
            ("Dash", self.get_dash_name()),
            ("Ultimate", self.get_ultimate_name()),
        ]

    def should_draw_tornado_effect(self):
        """Permite efeitos visuais persistentes específicos de uma ultimate."""
        return False

    def get_attack_sound(self):
        """Cada personagem pode tocar um som diferente no ataque básico."""
        return "shoot"

    def get_projectile_damage_multiplier(self):
        """Multiplicador simples para personalizar dano de personagens ranged."""
        return 1.0

    def on_dash_start(self, particles_group):
        """Hook chamado no momento exato em que o dash é iniciado."""
        return

    def on_dash_update(self, dt, combat_context):
        """Hook executado enquanto o dash permanece ativo."""
        return

    def update_ultimate_effects(self, combat_context):
        """Processa efeitos contínuos de ultimate.

        A maioria dos personagens não precisa de processamento por frame, então o
        comportamento padrão simplesmente não faz nada.
        """

        return CharacterActionFeedback()

    def _build_action_feedback(self, sound_name="", log_text="", log_color=(220, 220, 220)):
        """Pequeno helper para padronizar retornos de ações do personagem."""

        return CharacterActionFeedback(True, sound_name, log_text, log_color)

    def _attack_vectors(self, base_direction, projectile_count):
        """Gera os vetores usados em ataques com múltiplos projéteis.

        O leque de disparo fica centralizado no alvo principal, mantendo o mesmo
        comportamento que o jogo já possuía antes da refatoração.
        """

        for index in range(projectile_count):
            angle = -(15 * (projectile_count - 1)) / 2 + (index * 15)
            yield base_direction.rotate(angle)

    def start_dash(self, particles_group):
        """Ativa o dash respeitando cooldown e i-frames.

        Em vez de retornar apenas True/False, devolvemos um objeto de feedback
        para a HUD e o sistema de sons reagirem sem lógica duplicada.
        """

        if self.dash_cooldown_timer > 0:
            return CharacterActionFeedback()

        self.dash_active = True
        self.dash_timer = self.dash_duration
        self.dash_cooldown_timer = self.dash_cooldown
        self.iframes = self.dash_duration + 0.1
        self.on_dash_start(particles_group)
        return self._build_action_feedback(
            sound_name="dash",
            log_text=f"Skill: {self.get_dash_name()}",
            log_color=(80, 180, 255),
        )

    def update(self, dt, keys, obstacles, particles_group, biome_type="normal", combat_context=None):
        """Atualiza movimentação, colisão, animação e timers comuns.

        A lógica central ficou aqui porque é igual para todos os personagens.
        O que muda por personagem entra pelos hooks de dash e ultimate.
        """

        self.vel = pygame.Vector2(0, 0)

        if self.dash_active:
            self.dash_timer -= dt
            if random.random() < 0.5:
                particles_group.add(self.deps.particle_cls(self.pos, (200, 200, 200), 5, 50, 0.3))
            self.on_dash_update(dt, combat_context)
            if self.dash_timer <= 0:
                self.dash_active = False

        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt

        if self.ult_active_timer > 0:
            self.ult_active_timer -= dt
            if self.ult_active_timer <= 0:
                self.ult_active = False

        movement = pygame.Vector2(0, 0)
        if self.deps.control_reader(keys, "up"):
            movement.y -= 1
        if self.deps.control_reader(keys, "down"):
            movement.y += 1
        if self.deps.control_reader(keys, "left"):
            movement.x -= 1
        if self.deps.control_reader(keys, "right"):
            movement.x += 1

        if movement.length_squared() > 0:
            current_speed = self.dash_speed if self.dash_active else self.base_speed
            self.vel = movement.normalize() * current_speed

            if movement.x > 0:
                self.facing_right = True
            elif movement.x < 0:
                self.facing_right = False

            move = self.vel * dt
            self.pos.x += move.x
            for obstacle in obstacles:
                if obstacle.hitbox.collidepoint(self.pos):
                    self.pos.x -= move.x

            self.pos.y += move.y
            for obstacle in obstacles:
                if obstacle.hitbox.collidepoint(self.pos):
                    self.pos.y -= move.y

            self.anim_timer += dt
            if self.anim_timer > 0.08:
                self.anim_timer = 0
                self.frame_idx = (self.frame_idx + 1) % len(self.anim_frames)
        else:
            self.frame_idx = 0

        frame_set = self.anim_frames if self.facing_right else self.flipped_frames
        self.image = frame_set[self.frame_idx]
        self.iframes = max(0, self.iframes - dt)

        screen_w, screen_h = self.deps.screen_size_getter()
        self.rect.center = (screen_w // 2, screen_h // 2)

    def atacar(self, target, combat_context):
        """Executa o ataque básico padrão para personagens ranged.

        O loop principal não precisa mais saber se o personagem é corpo a corpo
        ou à distância. Ele apenas chama `atacar()` e deixa a subclasse decidir
        como materializar esse ataque.
        """

        if target is None:
            return CharacterActionFeedback()

        base_direction = target.pos - self.pos
        if base_direction.length_squared() <= 0:
            return CharacterActionFeedback()

        base_direction = base_direction.normalize()
        for direction in self._attack_vectors(base_direction, combat_context.projectile_count):
            shoot_angle = math.degrees(math.atan2(-direction.y, direction.x))
            if combat_context.bazooka_active:
                rotated_frames = [
                    pygame.transform.scale(pygame.transform.rotate(frame, shoot_angle), (300, 300))
                    for frame in combat_context.projectile_frames_raw
                ]
                projectile_damage = combat_context.projectile_damage * 3
            else:
                rotated_frames = [
                    pygame.transform.rotate(frame, shoot_angle)
                    for frame in combat_context.projectile_frames_raw
                ]
                projectile_damage = combat_context.projectile_damage

            projectile_damage *= self.get_projectile_damage_multiplier()
            projectile_damage = int(projectile_damage * combat_context.fury_multiplier)
            projectile = self.deps.projectile_cls(
                self.pos,
                direction * combat_context.projectile_speed,
                projectile_damage,
                rotated_frames,
            )
            combat_context.projectiles.add(projectile)

        return self._build_action_feedback(sound_name=self.get_attack_sound())

    @abstractmethod
    def use_ultimate(self, combat_context):
        """Ativa a ultimate específica de cada personagem."""


class Warrior(Player):
    """Personagem corpo a corpo focado em pressão próxima e área persistente."""

    def get_attack_name(self):
        return "Corte Giratório"

    def get_dash_name(self):
        return "Investida Guardiã"

    def get_ultimate_name(self):
        return "Tornado de Lâminas"

    def get_attack_sound(self):
        return "slash"

    def should_draw_tornado_effect(self):
        return True

    def atacar(self, target, combat_context):
        """Sobrescreve o ataque básico para gerar golpes melee em arco."""

        if target is None:
            return CharacterActionFeedback()

        base_direction = target.pos - self.pos
        if base_direction.length_squared() <= 0:
            return CharacterActionFeedback()

        base_direction = base_direction.normalize()
        for direction in self._attack_vectors(base_direction, combat_context.projectile_count):
            melee_damage = int((combat_context.projectile_damage + 2) * combat_context.fury_multiplier)
            combat_context.projectiles.add(
                self.deps.melee_slash_cls(self, direction, melee_damage, combat_context.slash_frames_raw)
            )

        return self._build_action_feedback(sound_name=self.get_attack_sound())

    def use_ultimate(self, combat_context):
        if self.ult_charge < self.ult_max:
            return CharacterActionFeedback()

        self.ult_charge = 0
        self.ult_active = True
        self.ult_active_timer = 3.0
        return self._build_action_feedback(
            log_text=f"Ultimate: {self.get_ultimate_name()}",
            log_color=(255, 90, 90),
        )

    def update_ultimate_effects(self, combat_context):
        """Enquanto o tornado estiver ativo, ele causa dano e gera feedback visual."""

        if not self.ult_active:
            return CharacterActionFeedback()

        kills_gained = 0
        if random.random() < 0.8:
            combat_context.particles.add(
                self.deps.particle_cls(
                    self.pos + pygame.Vector2(random.randint(-100, 100), random.randint(-100, 100)),
                    (200, 200, 255),
                    6,
                    200,
                    0.4,
                )
            )

        for enemy in combat_context.enemies:
            if self.pos.distance_to(enemy.pos) < 250:
                enemy.hp -= 2
                if random.random() < 0.2:
                    combat_context.damage_texts.add(
                        self.deps.damage_text_cls(enemy.pos, 2, False, (255, 255, 0))
                    )
                if enemy.hp <= 0:
                    if self.ult_charge < self.ult_max:
                        self.ult_charge += 1
                    combat_context.gems.add(self.deps.gem_cls(enemy.pos, combat_context.loader))
                    enemy.kill()
                    kills_gained += 1

        return CharacterActionFeedback(kills_gained=kills_gained)


class Assassin(Player):
    """Personagem móvel e agressivo, com dash ofensivo e explosão radial."""

    def __init__(self, loader, char_id, dependencies):
        super().__init__(loader, char_id, dependencies)
        self._dash_hit_targets = set()

    def get_attack_name(self):
        return "Rajada Precisa"

    def get_dash_name(self):
        return "Passo Sombrio"

    def get_ultimate_name(self):
        return "Chuva de Flechas"

    def on_dash_start(self, particles_group):
        self._dash_hit_targets.clear()

    def on_dash_update(self, dt, combat_context):
        """Durante o dash, o assassino corta inimigos atravessados pela corrida."""

        if combat_context is None or not combat_context.enemies:
            return

        dash_damage = int(self.base_damage * 2 + 2)
        for enemy in combat_context.enemies:
            if enemy in self._dash_hit_targets:
                continue
            if self.pos.distance_to(enemy.pos) <= 110:
                enemy.hp -= dash_damage
                self._dash_hit_targets.add(enemy)
                if combat_context.damage_texts is not None:
                    combat_context.damage_texts.add(
                        self.deps.damage_text_cls(enemy.pos, dash_damage, False, (255, 120, 120))
                    )

    def get_projectile_damage_multiplier(self):
        return 1.1

    def use_ultimate(self, combat_context):
        if self.ult_charge < self.ult_max:
            return CharacterActionFeedback()

        self.ult_charge = 0
        for index in range(36):
            angle = index * 10
            direction = pygame.Vector2(1, 0).rotate(angle)
            shoot_angle = math.degrees(math.atan2(-direction.y, direction.x))
            rotated_frames = [
                pygame.transform.rotate(frame, shoot_angle)
                for frame in combat_context.projectile_frames_raw
            ]
            projectile = self.deps.projectile_cls(
                self.pos,
                direction * combat_context.projectile_speed,
                int(combat_context.projectile_damage * 3 * self.get_projectile_damage_multiplier()),
                rotated_frames,
            )
            projectile.pierce = 5
            combat_context.projectiles.add(projectile)

        return self._build_action_feedback(
            log_text=f"Ultimate: {self.get_ultimate_name()}",
            log_color=(255, 170, 80),
        )


class Mage(Player):
    """Personagem de controle, com foco em utilidade e congelamento de massa."""

    def get_attack_name(self):
        return "Orbe Arcano"

    def get_dash_name(self):
        return "Passo Arcano"

    def get_ultimate_name(self):
        return "Congelamento Temporal"

    def use_ultimate(self, combat_context):
        if self.ult_charge < self.ult_max:
            return CharacterActionFeedback()

        self.ult_charge = 0
        for enemy in combat_context.enemies:
            enemy.frozen_timer = 5.0

        return self._build_action_feedback(
            log_text=f"Ultimate: {self.get_ultimate_name()}",
            log_color=(120, 220, 255),
        )


PLAYER_CLASS_FACTORY = {
    0: Warrior,
    1: Assassin,
    2: Mage,
}


def create_player(loader, char_id, dependencies):
    """Factory central para construir o personagem correto a partir do char_id."""

    safe_char_id = char_id if char_id in dependencies.char_data_map else 0
    player_cls = PLAYER_CLASS_FACTORY.get(safe_char_id, Warrior)
    return player_cls(loader, safe_char_id, dependencies)
