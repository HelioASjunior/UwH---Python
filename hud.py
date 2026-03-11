import os
import pygame

UI_THEME = {
    "void_black": (26, 26, 26),
    "charcoal": (34, 34, 34),
    "iron": (78, 74, 69),
    "old_gold": (184, 134, 72),
    "faded_gold": (156, 126, 74),
    "blood_red": (139, 0, 0),
    "mana_blue": (70, 110, 160),
    "parchment": (210, 198, 170),
    "mist": (210, 210, 210),
}

_font_cache = {}
skill_feed = []
upgrade_notifications = []
ui_visual_state = {"char_id": None, "hp": None, "mana": None}


def reset_feedback():
    global skill_feed, upgrade_notifications, ui_visual_state
    skill_feed = []
    upgrade_notifications = []
    ui_visual_state = {"char_id": None, "hp": None, "mana": None}


def load_dark_font(size, bold=False, asset_dir="assets"):
    cache_key = (asset_dir, size, bold)
    if cache_key in _font_cache:
        return _font_cache[cache_key]

    font_path = os.path.join(asset_dir, "fonts", "fonte_dark.ttf")
    try:
        if os.path.exists(font_path):
            font = pygame.font.Font(font_path, size)
        else:
            font = pygame.font.SysFont("georgia", size)
        font.set_bold(bold)
    except Exception:
        font = pygame.font.SysFont("georgia", size)
        font.set_bold(bold)

    _font_cache[cache_key] = font
    return font


def push_skill_feed(text, color=(220, 220, 220), duration=4.0):
    global skill_feed
    if not text:
        return
    skill_feed.insert(0, {"text": text, "color": color, "timer": duration})
    skill_feed = skill_feed[:8]


def push_upgrade_notification(text, color=None, duration=4.5):
    global upgrade_notifications
    if not text:
        return
    upgrade_notifications.insert(0, {
        "text": text,
        "color": color or UI_THEME["faded_gold"],
        "timer": duration,
        "max_timer": duration,
    })
    upgrade_notifications = upgrade_notifications[:5]


def smooth_ui_value(current_value, target_value, dt, speed=8.0):
    if current_value is None:
        return target_value
    blend = min(1.0, speed * dt)
    return current_value + (target_value - current_value) * blend


def update_feedback(dt):
    global skill_feed, upgrade_notifications

    active_entries = []
    for entry in skill_feed:
        entry["timer"] -= dt
        if entry["timer"] > 0:
            active_entries.append(entry)
    skill_feed = active_entries

    active_upgrade_notifications = []
    for entry in upgrade_notifications:
        entry["timer"] -= dt
        if entry["timer"] > 0:
            active_upgrade_notifications.append(entry)
    upgrade_notifications = active_upgrade_notifications


def draw_dark_panel(screen, rect, alpha=180, border_color=None):
    panel_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel_surface.fill((UI_THEME["void_black"][0], UI_THEME["void_black"][1], UI_THEME["void_black"][2], alpha))
    screen.blit(panel_surface, rect.topleft)
    pygame.draw.rect(screen, border_color or UI_THEME["iron"], rect, 2, border_radius=12)
    inner_rect = rect.inflate(-6, -6)
    pygame.draw.rect(screen, UI_THEME["charcoal"], inner_rect, 1, border_radius=10)


def draw_metallic_bar(screen, rect, display_value, max_value, fill_color, label, font_s, font_m, current_value=None):
    safe_max_value = max(1.0, max_value)
    display_ratio = max(0.0, min(1.0, display_value / safe_max_value))
    current_ratio = max(0.0, min(1.0, (current_value if current_value is not None else display_value) / safe_max_value))

    outer_rect = pygame.Rect(rect)
    draw_dark_panel(screen, outer_rect, alpha=185, border_color=UI_THEME["old_gold"])

    fill_area = outer_rect.inflate(-10, -12)
    pygame.draw.rect(screen, UI_THEME["void_black"], fill_area, border_radius=8)
    pygame.draw.rect(screen, (55, 20, 20) if fill_color == UI_THEME["blood_red"] else (20, 28, 45), fill_area, 1, border_radius=8)

    current_rect = fill_area.copy()
    current_rect.width = int(fill_area.width * current_ratio)
    pygame.draw.rect(screen, tuple(min(255, c + 30) for c in fill_color), current_rect, border_radius=8)

    display_rect = fill_area.copy()
    display_rect.width = int(fill_area.width * display_ratio)
    pygame.draw.rect(screen, fill_color, display_rect, border_radius=8)

    if display_rect.width > 8:
        highlight = pygame.Surface((display_rect.width, display_rect.height), pygame.SRCALPHA)
        highlight.fill((255, 255, 255, 24))
        screen.blit(highlight, display_rect.topleft)

    # Textos renderizados por último (acima da barra).
    # Ambos usam font_s para caber dentro do fill_area sem vazar.
    # Centralizados verticalmente e com drop shadow de 1px para contraste.
    value_str = f"{int(max(0, current_value if current_value is not None else display_value))}"
    label_surf = font_s.render(label, True, UI_THEME["parchment"])
    value_surf = font_s.render(value_str, True, UI_THEME["mist"])

    label_x = fill_area.x + 8
    label_y = fill_area.y + (fill_area.height - label_surf.get_height()) // 2
    value_x = fill_area.right - value_surf.get_width() - 8
    value_y = fill_area.y + (fill_area.height - value_surf.get_height()) // 2

    _sh = (0, 0, 0)
    screen.blit(font_s.render(label, True, _sh), (label_x + 1, label_y + 1))
    screen.blit(label_surf, (label_x, label_y))
    screen.blit(font_s.render(value_str, True, _sh), (value_x + 1, value_y + 1))
    screen.blit(value_surf, (value_x, value_y))


def draw_skill_feed_panel(screen, player, font_s, hud_scale, high_contrast, screen_w, screen_h=720):
    if not player:
        return

    # Layout dinâmico do grimório:
    #
    # 1) medimos a largura de todas as linhas relevantes;
    # 2) aplicamos padding para construir uma moldura que não corte texto;
    # 3) usamos line_spacing fixo para impedir sobreposição.
    pad_x = 20
    pad_y = 14
    line_spacing = max(24, int(30 * hud_scale))
    section_gap = max(12, int(14 * hud_scale))
    anchor_offset = 10

    title_text = "GRIMORIO DE BATALHA"
    recent_title_text = "MAGIAS RECENTES"
    skill_lines = [f"{label.upper()}: {value}" for label, value in player.get_skill_cards()]
    recent_lines = [entry["text"] for entry in skill_feed[:4]]

    measured_lines = [title_text, recent_title_text] + skill_lines + recent_lines
    longest_width = 0
    for line in measured_lines:
        line_surface = font_s.render(line, True, UI_THEME["mist"])
        longest_width = max(longest_width, line_surface.get_width())

    panel_w = longest_width + pad_x * 2
    skill_block_h = line_spacing * max(1, len(skill_lines))
    recent_block_h = line_spacing * max(1, len(recent_lines))
    panel_h = (
        pad_y
        + line_spacing
        + 6
        + section_gap
        + skill_block_h
        + section_gap
        + line_spacing
        + 6
        + section_gap
        + recent_block_h
        + pad_y
    )

    # Âncora: canto inferior esquerdo com margem fixa de 20px.
    panel_x = 20
    panel_y = screen_h - panel_h - 20
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    border_color = UI_THEME["old_gold"] if not high_contrast else (255, 255, 255)
    title_color = UI_THEME["old_gold"] if not high_contrast else (255, 255, 0)
    text_color = UI_THEME["mist"] if not high_contrast else (255, 255, 255)

    draw_dark_panel(screen, panel_rect, alpha=180, border_color=border_color)

    cursor_y = panel_rect.y + pad_y

    # Título principal + separador
    title_surf = font_s.render(title_text, True, title_color)
    screen.blit(title_surf, (panel_rect.x + pad_x, cursor_y))
    cursor_y += line_spacing
    pygame.draw.line(
        screen,
        UI_THEME["faded_gold"],
        (panel_rect.x + pad_x, cursor_y - 6),
        (panel_rect.right - pad_x, cursor_y - 6),
        1,
    )
    cursor_y += section_gap

    # Linhas do grimório (todas alinhadas à esquerda)
    for line in skill_lines:
        line_surf = font_s.render(line, True, text_color)
        screen.blit(line_surf, (panel_rect.x + pad_x, cursor_y))
        cursor_y += line_spacing

    cursor_y += section_gap

    # Subtítulo de magias recentes + separador
    recent_title_surf = font_s.render(recent_title_text, True, title_color)
    screen.blit(recent_title_surf, (panel_rect.x + pad_x, cursor_y))
    cursor_y += line_spacing
    pygame.draw.line(
        screen,
        UI_THEME["faded_gold"],
        (panel_rect.x + pad_x, cursor_y - 6),
        (panel_rect.right - pad_x, cursor_y - 6),
        1,
    )
    cursor_y += section_gap

    # Entradas recentes com fade-out e espaçamento constante
    if not recent_lines:
        empty_surf = font_s.render("Sem magias recentes", True, UI_THEME["iron"])
        screen.blit(empty_surf, (panel_rect.x + pad_x, cursor_y))
    else:
        for entry in skill_feed[:4]:
            alpha_ratio = max(0.18, min(1.0, entry["timer"] / 4.0))
            color = tuple(int(channel * alpha_ratio) for channel in entry["color"])
            text_surface = font_s.render(entry["text"], True, color)
            screen.blit(text_surface, (panel_rect.x + pad_x, cursor_y))
            cursor_y += line_spacing


def draw_upgrade_notifications(screen, font_s):
    start_x = 28
    start_y = 220
    for index, entry in enumerate(upgrade_notifications[:4]):
        alpha_ratio = max(0.0, min(1.0, entry["timer"] / max(0.01, entry["max_timer"])))
        bg_alpha = int(155 * alpha_ratio)
        text_alpha = int(255 * alpha_ratio)
        text_surface = font_s.render(entry["text"], True, entry["color"])
        text_surface.set_alpha(text_alpha)

        box_rect = pygame.Rect(start_x, start_y + index * 38, text_surface.get_width() + 28, 30)
        bg_surface = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        bg_surface.fill((UI_THEME["charcoal"][0], UI_THEME["charcoal"][1], UI_THEME["charcoal"][2], bg_alpha))
        screen.blit(bg_surface, box_rect.topleft)
        pygame.draw.rect(screen, UI_THEME["faded_gold"], box_rect, 1, border_radius=8)
        screen.blit(text_surface, (box_rect.x + 12, box_rect.y + 5))


def draw_ui(screen, player, state, font_s, font_m, font_l, hud_scale, high_contrast, level, xp, current_xp_to_level, game_time, kills, dt, screen_w, screen_h, player_max_hp, game_version, build_type, player_upgrades):
    version_str = f"v{game_version} ({build_type})"
    version_shadow = font_s.render(version_str, True, (0, 0, 0))
    version_text = font_s.render(version_str, True, UI_THEME["iron"])
    version_rect = version_text.get_rect(bottomright=(screen_w - 12, screen_h - 10))

    if player and state in ["PLAYING", "UPGRADE", "CHEST_UI", "PAUSED", "GAME_OVER"]:
        if ui_visual_state["char_id"] != player.char_id:
            ui_visual_state["char_id"] = player.char_id
            ui_visual_state["hp"] = float(player.hp)
            ui_visual_state["mana"] = float(player.ult_charge)

        ui_visual_state["hp"] = smooth_ui_value(ui_visual_state["hp"], float(player.hp), dt)
        ui_visual_state["mana"] = smooth_ui_value(ui_visual_state["mana"], float(player.ult_charge), dt)

        bar_w = int(270 * hud_scale)
        bar_h = int(44 * hud_scale)   # 44px garante margem confortável para font_s (24px)
        hp_rect = pygame.Rect(20, 22, bar_w, bar_h)
        mana_rect = pygame.Rect(20, 22 + bar_h + 10, bar_w, bar_h)

        draw_metallic_bar(screen, hp_rect, ui_visual_state["hp"], player_max_hp, UI_THEME["blood_red"], "HP", font_s, font_m, current_value=player.hp)
        draw_metallic_bar(screen, mana_rect, ui_visual_state["mana"], player.ult_max, UI_THEME["mana_blue"], "MANA", font_s, font_m, current_value=player.ult_charge)

        time_m, time_s = divmod(int(game_time), 60)
        top_panel = pygame.Rect(screen_w // 2 - 150, 18, 300, 42)
        draw_dark_panel(screen, top_panel, alpha=180, border_color=UI_THEME["iron"])
        time_text = font_s.render(f"{time_m:02}:{time_s:02}  |  KILLS {kills}", True, UI_THEME["parchment"])
        screen.blit(time_text, time_text.get_rect(center=top_panel.center))

        xp_panel = pygame.Rect(0, 0, screen_w, 14)
        xp_surface = pygame.Surface((xp_panel.width, xp_panel.height), pygame.SRCALPHA)
        xp_surface.fill((UI_THEME["void_black"][0], UI_THEME["void_black"][1], UI_THEME["void_black"][2], 210))
        screen.blit(xp_surface, xp_panel.topleft)
        xp_ratio = 0 if current_xp_to_level <= 0 else max(0.0, min(1.0, xp / current_xp_to_level))
        pygame.draw.rect(screen, UI_THEME["faded_gold"], (0, 0, int(screen_w * xp_ratio), 14))
        level_text = font_s.render(f"NIVEL {level}", True, UI_THEME["mist"])
        screen.blit(level_text, (screen_w - level_text.get_width() - 14, 16))

        draw_skill_feed_panel(screen, player, font_s, hud_scale, high_contrast, screen_w, screen_h)

        if player_upgrades:
            upgrades_preview = ", ".join(player_upgrades[-3:])
            preview = font_s.render(f"ULTIMOS UPS: {upgrades_preview}", True, UI_THEME["faded_gold"])
            screen.blit(preview, (24, 120))

        draw_upgrade_notifications(screen, font_s)

    screen.blit(version_shadow, (version_rect.x + 1, version_rect.y + 1))
    screen.blit(version_text, version_rect)
