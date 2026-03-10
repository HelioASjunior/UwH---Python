import math
import random
import pygame
import os
import json
from datetime import datetime, timedelta

# =========================================================
# CONFIGURAÇÕES DE PERSISTÊNCIA (SETTINGS.JSON)
# =========================================================

def load_settings(force_default=False):
    default_settings = {
        "video": {
            "resolution": "1920x1080",
            "fullscreen": "Off",
            "vsync": "Off",
            "fps_limit": 60,
            "show_fps": "Off"
        },
        "audio": {
            "music": 70,
            "sfx": 80,
            "mute": "Off"
        },
        "controls": {
            "up": "w",
            "down": "s",
            "left": "a",
            "right": "d",
            "dash": "space",
            "ultimate": "e",
            "pause": "p"
        },
        "gameplay": {
            "auto_pickup_chest": "On",
            "auto_apply_chest_reward": "On",
            "show_offscreen_arrows": "On",
            "default_difficulty": "Médio"
        },
        "accessibility": {
            "screen_shake": 100,
            "ui_size": 100,
            "high_contrast": "Off"
        }
    }

    if force_default:
        return json.loads(json.dumps(default_settings))

    if os.path.exists("settings.json"):
        try:
            with open("settings.json", "r") as f:
                loaded = json.load(f)

            # Migra formatos antigos (flat) para o formato atual por categoria.
            if "video" not in loaded:
                loaded = {
                    "video": {
                        "resolution": f"{loaded.get('resolution', [1920, 1080])[0]}x{loaded.get('resolution', [1920, 1080])[1]}",
                        "fullscreen": "On" if loaded.get("fullscreen", False) else "Off",
                        "vsync": "Off",
                        "fps_limit": 60,
                        "show_fps": "Off"
                    },
                    "audio": {
                        "music": int(loaded.get("music_volume", 0.7) * 100),
                        "sfx": int(loaded.get("sfx_volume", 0.8) * 100),
                        "mute": "Off"
                    },
                    "controls": default_settings["controls"],
                    "gameplay": default_settings["gameplay"],
                    "accessibility": {
                        "screen_shake": 100 if loaded.get("screen_shake", True) else 0,
                        "ui_size": 100,
                        "high_contrast": "Off"
                    }
                }

            merged = json.loads(json.dumps(default_settings))
            for cat, values in loaded.items():
                if cat in merged and isinstance(values, dict):
                    merged[cat].update(values)
            return merged
        except Exception:
            return json.loads(json.dumps(default_settings))

    return load_settings(force_default=True)


def save_settings(settings):
    with open("settings.json", "w") as f:
        json.dump(settings, f, indent=4)


def _deepcopy_settings(src):
    return json.loads(json.dumps(src))


def get_control_key_code(action_name):
    if not settings or "controls" not in settings:
        return pygame.K_UNKNOWN
    key_name = settings["controls"].get(action_name, "")
    try:
        return pygame.key.key_code(key_name)
    except Exception:
        return pygame.K_UNKNOWN


def is_control_pressed(keys, action_name):
    key_code = get_control_key_code(action_name)
    if key_code == pygame.K_UNKNOWN:
        return False
    return keys[key_code]


def apply_audio_runtime(settings_dict):
    global MUSIC_VOLUME, SFX_VOLUME
    MUSIC_VOLUME = settings_dict["audio"].get("music", 100) / 100.0
    SFX_VOLUME = settings_dict["audio"].get("sfx", 100) / 100.0
    if settings_dict["audio"].get("mute") == "On":
        pygame.mixer.music.set_volume(0.0)
    else:
        pygame.mixer.music.set_volume(MUSIC_VOLUME)

def apply_settings(settings_dict):
    global SCREEN_W, SCREEN_H, screen, FPS, MUSIC_VOLUME, SFX_VOLUME
    res_w, res_h = map(int, settings_dict["video"]["resolution"].split('x'))
    SCREEN_W, SCREEN_H = res_w, res_h
    
    flags = 0
    if settings_dict["video"]["fullscreen"] == "On":
        flags = pygame.FULLSCREEN
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
    
    FPS = int(settings_dict["video"]["fps_limit"])
    
    apply_audio_runtime(settings_dict)

# =========================================================
# VARIÁVEIS GLOBAIS E INICIAIS (DO ORIGINAL)
# =========================================================
# =========================================================
# CONFIGURAÇÕES INICIAIS
# =========================================================
SCREEN_W, SCREEN_H = 1920, 1080
FPS = 60
ASSET_DIR = "assets" 
GAME_VERSION = "1.0.0"
BUILD_TYPE = "META"

# =========================================================
# META-PROGRESSÃO, SAVE E CONQUISTAS
# =========================================================
SAVE_FILE = "save_v2.json"
RUN_SLOT_FILES = ["run_slot_1.json", "run_slot_2.json", "run_slot_3.json"]

# Itens que começam desbloqueados
DEFAULT_UNLOCKS = [
    "DANO ++", "VELOCIDADE ++", "VIDA MÁXIMA", "TIRO RÁPIDO", "CURA",
    "CHAR_0", "DIFF_FÁCIL", "DIFF_MÉDIO"
]

save_data = {
    "gold": 0,
    "perm_upgrades": {
        "crit_dmg": 0, "exp_size": 0, "chaos_bolt": 0,
        "regen": 0, "aura_res": 0, "thorns": 0,
        "fire_dmg": 0, "burn_area": 0, "inferno": 0
    },
    "stats": {
        "total_kills": 0,
        "total_time": 0,
        "boss_kills": 0,
        "deaths": 0,
        "games_played": 0,
        "max_level_reached": 0
    },
    "unlocks": list(DEFAULT_UNLOCKS),
    "daily_missions": {
        "last_reset": "", # Data do último reset (YYYY-MM-DD)
        "active": []      # Lista de missões ativas hoje
    }
}

# Definição das Missões Diárias
DAILY_MISSIONS_POOL = [
    {"id": "kill_100", "name": "CAÇADOR DIÁRIO", "desc": "Mate 100 inimigos em uma partida", "goal": 100, "reward": 500, "type": "kills"},
    {"id": "survive_5m", "name": "SOBREVIVENTE", "desc": "Sobreviva por 5 minutos", "goal": 300, "reward": 800, "type": "time"},
    {"id": "boss_1", "name": "MATADOR DE GIGANTES", "desc": "Derrote 1 Chefão", "goal": 1, "reward": 1200, "type": "boss"},
    {"id": "level_15", "name": "TREINAMENTO INTENSO", "desc": "Alcance o Nível 15", "goal": 15, "reward": 1000, "type": "level"},
    {"id": "gold_200", "name": "GANÂNCIA", "desc": "Colete 200 de Ouro em uma partida", "goal": 200, "reward": 600, "type": "gold"}
]

# Definição das Conquistas e Requisitos
ACHIEVEMENTS = {
    "CHAR_1": {"type": "char", "name": "CAÇADOR", "desc": "Mate 500 inimigos no total", "req": lambda s: s["total_kills"] >= 500},
    "CHAR_2": {"type": "char", "name": "MAGO", "desc": "Derrote 1 Chefão", "req": lambda s: s["boss_kills"] >= 1},
    
    "DIFF_DIFÍCIL": {"type": "diff", "name": "DIFÍCIL", "desc": "Sobreviva 10 min (total)", "req": lambda s: s["total_time"] >= 600},
    "DIFF_HARDCORE": {"type": "diff", "name": "HARDCORE", "desc": "Derrote 5 Chefões", "req": lambda s: s["boss_kills"] >= 5},

    "TIRO MÚLTIPLO": {"type": "upg", "name": "TIRO MÚLTIPLO", "desc": "Alcance Nível 10 em uma partida", "req": lambda s: s["max_level_reached"] >= 10},
    "AURA MÁGICA": {"type": "upg", "name": "AURA MÁGICA", "desc": "Colete 200 Ouro no total", "req": lambda s: True}, # Desbloqueio fácil exemplo
    "EXPLOSÃO": {"type": "upg", "name": "EXPLOSÃO", "desc": "Mate 1000 inimigos no total", "req": lambda s: s["total_kills"] >= 1000},
    "ORBES MÁGICOS": {"type": "upg", "name": "ORBES MÁGICOS", "desc": "Jogue 3 partidas", "req": lambda s: s["games_played"] >= 3},
    "PERFURAÇÃO": {"type": "upg", "name": "PERFURAÇÃO", "desc": "Mate 1500 inimigos", "req": lambda s: s["total_kills"] >= 1500},
    "SORTE": {"type": "upg", "name": "SORTE", "desc": "Morra 1 vez (Piedade)", "req": lambda s: s["deaths"] >= 1},
    "RICOCHE": {"type": "upg", "name": "RICOCHE", "desc": "Desbloqueie o Caçador", "req": lambda s: "CHAR_1" in save_data["unlocks"]},
    "EXECUÇÃO": {"type": "upg", "name": "EXECUÇÃO", "desc": "Derrote 3 Chefões", "req": lambda s: s["boss_kills"] >= 3},
    "FÚRIA": {"type": "upg", "name": "FÚRIA", "desc": "Chegue a 10% de HP (em uma run)", "req": lambda s: True}, # Lógica especial ingame
    "ÍMÃ DE XP": {"type": "upg", "name": "ÍMÃ DE XP", "desc": "Sobreviva 5 min totais", "req": lambda s: s["total_time"] >= 300},
}

def load_save():
    global save_data
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                loaded = json.load(f)
                # Merge seguro para não perder chaves novas em updates
                if "gold" in loaded: save_data["gold"] = loaded["gold"]
                if "perm_upgrades" in loaded: save_data["perm_upgrades"].update(loaded["perm_upgrades"])
                if "stats" in loaded: save_data["stats"].update(loaded["stats"])
                if "unlocks" in loaded: 
                    for u in loaded["unlocks"]:
                        if u not in save_data["unlocks"]: save_data["unlocks"].append(u)
                if "daily_missions" in loaded:
                    save_data["daily_missions"].update(loaded["daily_missions"])
        except: pass
    check_daily_reset()

def check_daily_reset():
    global save_data
    today = datetime.now().strftime("%Y-%m-%d")
    if save_data["daily_missions"]["last_reset"] != today:
        save_data["daily_missions"]["last_reset"] = today
        # Sorteia 3 missões novas
        new_missions = random.sample(DAILY_MISSIONS_POOL, 3)
        save_data["daily_missions"]["active"] = []
        for m in new_missions:
            m_copy = m.copy()
            m_copy["progress"] = 0
            m_copy["completed"] = False
            m_copy["claimed"] = False
            save_data["daily_missions"]["active"].append(m_copy)
        save_game()

def update_mission_progress(m_type, amount, is_absolute=False):
    global save_data
    changed = False
    
    # Otimização: Throttling para missões de tempo (só processa a cada 1 segundo acumulado)
    if m_type == "time":
        if not hasattr(update_mission_progress, "_time_acc"): update_mission_progress._time_acc = 0.0
        update_mission_progress._time_acc += amount
        if update_mission_progress._time_acc < 1.0: return
        amount = update_mission_progress._time_acc
        update_mission_progress._time_acc = 0.0

    for m in save_data["daily_missions"]["active"]:
        if m["type"] == m_type and not m["completed"]:
            if is_absolute:
                m["progress"] = max(m["progress"], amount)
            else:
                m["progress"] += amount
            
            if m["progress"] >= m["goal"]:
                m["progress"] = m["goal"]
                m["completed"] = True
            changed = True
    
    # Otimização: Durante a partida, não salvamos no disco a cada pequena mudança de progresso
    # O progresso fica na memória e é salvo no final da partida ou ao sair do menu.
    # Apenas salvamos imediatamente se uma missão for COMPLETADA.
    if changed:
        any_completed = any(m["completed"] and not m.get("_notified", False) for m in save_data["daily_missions"]["active"])
        if any_completed:
            for m in save_data["daily_missions"]["active"]:
                if m["completed"]: m["_notified"] = True
            save_game()

def save_game():
    with open(SAVE_FILE, "w") as f:
        json.dump(save_data, f)


def get_run_slot_path(slot_index):
    idx = max(0, min(len(RUN_SLOT_FILES) - 1, slot_index))
    return RUN_SLOT_FILES[idx]


def save_run_slot(slot_index=0):
    if player is None:
        return False

    data = {
        "char_id": getattr(player, "char_id", 0),
        "selected_difficulty": selected_difficulty,
        "selected_pact": selected_pact,
        "selected_bg": selected_bg,
        "kills": kills,
        "game_time": game_time,
        "level": level,
        "xp": xp,
        "player_hp": player.hp,
        "player_upgrades": list(player_upgrades),
        "run_gold_collected": float(globals().get("run_gold_collected", 0.0)),
    }

    try:
        with open(get_run_slot_path(slot_index), "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception:
        return False


def load_run_slot(slot_index=0):
    global selected_difficulty, selected_pact, selected_bg
    global kills, game_time, level, xp, run_gold_collected

    path = get_run_slot_path(slot_index)
    if not os.path.exists(path):
        return False

    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception:
        return False

    try:
        char_id = int(data.get("char_id", 0))
        selected_difficulty = data.get("selected_difficulty", "MÉDIO")
        selected_pact = data.get("selected_pact", "NENHUM")
        selected_bg = data.get("selected_bg", "dungeon")
        load_all_assets()

        prev_games = save_data["stats"].get("games_played", 0)
        reset_game(char_id)
        save_data["stats"]["games_played"] = prev_games

        for upg in data.get("player_upgrades", []):
            apply_upgrade(upg)

        kills = int(data.get("kills", 0))
        game_time = float(data.get("game_time", 0.0))
        level = max(1, int(data.get("level", 1)))
        xp = int(data.get("xp", 0))
        if player:
            player.hp = max(0.1, min(PLAYER_MAX_HP, float(data.get("player_hp", PLAYER_MAX_HP))))

        run_gold_collected = float(data.get("run_gold_collected", 0.0))
        return True
    except Exception:
        return False

load_save() 

# Árvore de Talentos Avançada
TALENT_TREE = {
    "CAOS": {
        "title": "CAMINHO DO CAOS",
        "desc": "Foco em explosões e dano crítico.",
        "skills": {
            "crit_dmg": {"name": "GOLPE FATAL", "desc": "+20% Dano Crítico", "cost": [300, 600, 1200], "max": 3, "icon": "talent_chaos"},
            "exp_size": {"name": "INSTABILIDADE", "desc": "+15% Raio de Explosão", "cost": [400, 800, 1600], "max": 3, "icon": "talent_chaos"},
            "chaos_bolt": {"name": "FAÍSCA CAÓTICA", "desc": "Tiros têm chance de explodir", "cost": [1000], "max": 1, "icon": "talent_chaos"}
        }
    },
    "GUARDIÃO": {
        "title": "CAMINHO DO GUARDIÃO",
        "desc": "Foco em defesa, regeneração e aura.",
        "skills": {
            "regen": {"name": "VIGOR", "desc": "Cura 0.1 HP/seg", "cost": [500, 1000, 2000], "max": 3, "icon": "talent_guardian"},
            "aura_res": {"name": "ESCUDO ESPIRITUAL", "desc": "+10% Resistência a Dano", "cost": [400, 800, 1600], "max": 3, "icon": "talent_guardian"},
            "thorns": {"name": "ESPINHOS", "desc": "Reflete 20% do dano recebido", "cost": [1200], "max": 1, "icon": "talent_guardian"}
        }
    },
    "FOGO": {
        "title": "CAMINHO DO FOGO",
        "desc": "Foco em dano mágico e aura.",
        "skills": {
            "fire_dmg": {"name": "PIROMANCIA", "desc": "+15% Dano de Aura", "cost": [300, 600, 1200], "max": 3, "icon": "talent_fire"},
            "burn_area": {"name": "TERRA QUEIMADA", "desc": "+20% Área de Aura", "cost": [400, 800, 1600], "max": 3, "icon": "talent_fire"},
            "inferno": {"name": "INFERNO", "desc": "Inimigos na aura pegam fogo", "cost": [1500], "max": 1, "icon": "talent_fire"}
        }
    }
}

DIFFICULTIES = {
    "FÁCIL":    {"hp_mult": 0.7, "spd_mult": 0.8, "dmg_mult": 0.5, "gold_mult": 0.8, "color": (100, 255, 100), "desc": "Para relaxar. Inimigos fracos.", "id": "DIFF_FÁCIL"},
    "MÉDIO":    {"hp_mult": 1.0, "spd_mult": 1.0, "dmg_mult": 1.0, "gold_mult": 1.0, "color": (255, 255, 100), "desc": "A experiência padrão.", "id": "DIFF_MÉDIO"},
    "DIFÍCIL":  {"hp_mult": 1.5, "spd_mult": 1.15, "dmg_mult": 1.5, "gold_mult": 1.4, "color": (255, 150, 50), "desc": "Novos Monstros! +40% Ouro.", "id": "DIFF_DIFÍCIL"},
    "HARDCORE": {"hp_mult": 2.5, "spd_mult": 1.3, "dmg_mult": 2.0, "gold_mult": 2.0, "color": (255, 50, 50),   "desc": "Pesadelo. +100% Ouro.", "id": "DIFF_HARDCORE"}
}

# Atributos Modificáveis (Base)
PLAYER_SPEED = 280.0
PLAYER_MAX_HP = 5
SHOT_COOLDOWN = 0.35
HAS_FURY = False
PROJECTILE_DMG = 2
PROJECTILE_SPEED = 560.0
PICKUP_RANGE = 50.0 
AURA_DMG = 0        
AURA_RANGE = 200    
PROJ_COUNT = 1       
PROJ_PIERCE = 0
PROJ_RICOCHET = 0
EXPLOSION_RADIUS = 0 
EXPLOSION_DMG = 5    
ORB_COUNT = 0        
ORB_DMG = 6          
ORB_DISTANCE = 180   
CRIT_CHANCE = 0.05   
MUSIC_VOLUME = 0.4  
SFX_VOLUME = 0.6    
EXECUTE_THRESH = 0.0

# Configurações de Habilidades
DASH_SPEED = 900.0      
DASH_DURATION = 0.2     
DASH_COOLDOWN = 2.5
ULTIMATE_MAX_CHARGE = 25 

# Configuração de Drops e Boss
DROP_CHANCE = 0.012 
BOSS_SPAWN_TIME = 300.0 # 5 Minutos para cada boss
BOSS_MAX_HP = 500
SHOOTER_PROJ_IMAGE = "enemy_proj" 

# Dados dos Personagens
CHAR_DATA = {
    0: {"name": "GUERREIRO", "hp": 7, "speed": 280, "desc": "Ult: Tornado de Lâminas", "size": (200, 200), "menu_size": (280, 280), "id": "CHAR_0"},
    1: {"name": "CAÇADOR", "hp": 4, "speed": 340, "desc": "Ult: Chuva de Flechas", "size": (140, 140), "menu_size": (220, 220), "id": "CHAR_1"},
    2: {"name": "MAGO", "hp": 5, "speed": 260, "desc": "Ult: Congelamento Temporal", "size": (160, 160), "menu_size": (250, 250), "id": "CHAR_2"}
}

# Constantes
WORLD_GRID = 64
BG_COLOR = (14, 14, 18)
PLAYER_IFRAMES = 0.85
GEM_XP = 3
XP_TO_LEVEL_BASE = 100   
SHOT_RANGE = 600.0
SPAWN_EVERY_BASE = 0.2
MAX_UPGRADE_LEVEL = 5
GAME_VERSION = "1.0.0 (Closed Beta)"

# Pool Completa (Será filtrada pelo Unlock System)
ALL_UPGRADES_POOL = {
    "DANO ++": "Aumenta o dano dos projéteis em +2",
    "VELOCIDADE ++": "Aumenta a velocidade de movimento em 15%",
    "TIRO RÁPIDO": "Atira com mais frequência",
    "VIDA MÁXIMA": "Aumenta o HP máximo e cura +1",
    "AURA MÁGICA": "Dano contínuo ao redor do jogador",
    "ÍMÃ DE XP": "Aumenta muito o raio de coleta",
    "TIRO MÚLTIPLO": "Atira projéteis adicionais em leque",
    "EXPLOSÃO": "Tiros explodem ao atingir o alvo",
    "PERFURAÇÃO": "O projétil atravessa +1 inimigo",
    "ORBES MÁGICOS": "Esferas giratórias protegem você",
    "SORTE": "Aumenta a Chance de Crítico em +10%",
    "CURA": "Recupera todo o HP atual",
    "RICOCHE": "Projéteis quicam em +1 inimigo próximo",
    "EXECUÇÃO": "Inimigos abaixo de 12% de vida morrem instantaneamente",
    "FÚRIA": "Quanto menor seu HP, maior dano e cadência (até +60%)",
    "CAPA INVISÍVEL": "10% de chance de inimigos não te notarem",
    "LUVA EXPULSÃO": "Aumenta muito o empurrão (Knockback)",
    "TREVO SORTE": "Aumenta a raridade dos upgrades",
}

UPGRADE_TAGS = {
    "DANO ++": {"dano"},
    "TIRO RÁPIDO": {"cadencia"},
    "VELOCIDADE ++": {"movimento"},
    "TIRO MÚLTIPLO": {"projeteis"},
    "PERFURAÇÃO": {"projeteis"},
    "EXPLOSÃO": {"explosao"},
    "AURA MÁGICA": {"aura"},
    "ÍMÃ DE XP": {"magnetismo"},
    "ORBES MÁGICOS": {"orbes"},
    "SORTE": {"critico"},
    "VIDA MÁXIMA": {"tank"},
    "CURA": {"sobrevivencia"},
    "RICOCHE": {"projeteis"},
    "EXECUÇÃO": {"dano"},
    "FÚRIA": {"tank"},
    "CAPA INVISÍVEL": {"sobrevivencia"},
    "LUVA EXPULSÃO": {"defesa"},
    "TREVO SORTE": {"utilidade"},
}

EVOLUTIONS = {
    "BAZUCA": {"base": "TIRO MÚLTIPLO", "passive": "EXPLOSÃO", "desc": "EVOLUÇÃO: Tiros gigantes, massivos e explosivos!"},
    "BURACO NEGRO": {"base": "AURA MÁGICA", "passive": "ÍMÃ DE XP", "desc": "EVOLUÇÃO: Aura magnética que suga e esmaga inimigos!"},
    "SERRAS MÁGICAS": {"base": "ORBES MÁGICOS", "passive": "VELOCIDADE ++", "desc": "EVOLUÇÃO: Orbes giram freneticamente rasgando tudo!"},
    "TESLA": {"base": "TIRO RÁPIDO", "passive": "RICOCHE", "desc": "EVOLUÇÃO: Raios em cadeia entre inimigos!"},
    "CEIFADOR": {"base": "EXECUÇÃO", "passive": "SORTE", "desc": "EVOLUÇÃO: Execução brutal + críticos insanos!"},
    "BERSERK": {"base": "FÚRIA", "passive": "VIDA MÁXIMA", "desc": "EVOLUÇÃO: Quanto mais apanha, mais destrói tudo!"},
}

UPGRADE_ICONS = {
    "DANO ++": "icon_damage",
    "VELOCIDADE ++": "icon_speed",
    "TIRO RÁPIDO": "icon_firespeed",
    "VIDA MÁXIMA": "icon_hp",
    "AURA MÁGICA": "icon_aura",
    "ÍMÃ DE XP": "icon_magnet",
    "TIRO MÚLTIPLO": "icon_multishot",
    "EXPLOSÃO": "icon_explosion",
    "PERFURAÇÃO": "icon_pierce",
    "ORBES MÁGICOS": "icon_orbs",
    "SORTE": "icon_luck",
    "CURA": "icon_heal",
    "BAZUCA": "icon_bazuca",
    "BURACO NEGRO": "icon_blackhole",
    "SERRAS MÁGICAS": "icon_saws",
    "RICOCHE": "icon_ricochet",
    "EXECUÇÃO": "icon_execute",
    "FÚRIA": "icon_fury",
    "CAPA INVISÍVEL": "item_capa",
    "LUVA EXPULSÃO": "item_luva",
    "TREVO SORTE": "item_trevo",
    "SYNERGY_MIDAS": "synergy_midas"
}
RARITY = {
    "COMUM": {"chance": 0.72, "mult": 1.0, "color": (200,200,200)},
    "RARO":  {"chance": 0.23, "mult": 1.35, "color": (80,170,255)},
    "EPICO": {"chance": 0.05, "mult": 1.75, "color": (200,80,255)},
}

# Alias para compatibilidade (RARITIES = RARITY)
RARITIES = RARITY

# Pool de upgrades disponíveis (filtrada pelos unlocks)
UPGRADE_POOL = {k: v for k, v in ALL_UPGRADES_POOL.items() if k in DEFAULT_UNLOCKS or True}

# Pactos disponíveis
PACTOS = {
    "NENHUM":     {"name": "SEM PACTO",       "desc": "Sem modificadores.",                     "hp": 0,  "color": (200, 200, 200)},
    "VELOCIDADE": {"name": "PACTO DA PRESSA",  "desc": "Inimigos 50% mais rápidos, +50% Ouro.",  "hp": 0,  "color": (255, 200, 0)},
    "FRÁGIL":     {"name": "PACTO FRÁGIL",     "desc": "Começa com -2 HP máximo, +30% XP.",       "hp": -2, "color": (255, 100, 100)},
    "SOMBRA":     {"name": "PACTO DA SOMBRA",  "desc": "Inimigos invisíveis, +80% Ouro.",          "hp": 0,  "color": (150, 0, 200)},
}

# Dados dos biomas / backgrounds
BG_DATA = {
    "dungeon":  {"name": "bg_dungeon",  "music": "music_dungeon",  "type": "normal"},
    "forest":   {"name": "bg_forest",   "music": "music_forest",   "type": "normal"},
    "volcano":  {"name": "bg_volcano",  "music": "music_volcano",  "type": "volcano"},
    "ice":      {"name": "bg_ice",      "music": "music_ice",      "type": "ice"},
}

# Multiplicadores permanentes (serão sobrescritos em reset_game)
CRIT_DMG_MULT = 2.0
EXPLOSION_SIZE_MULT = 1.0
REGEN_RATE = 0.0
DAMAGE_RES = 0.0
THORNS_PERCENT = 0.0
FIRE_DMG_MULT = 1.0
BURN_AURA_MULT = 1.0
HAS_CHAOS_BOLT = False
HAS_INFERNO = False

def roll_rarity(player_upgrades=None):
    r = random.random()
    
    # Trevo da Sorte: Aumenta chance de raridades altas
    if player_upgrades and "TREVO SORTE" in player_upgrades:
        r *= 0.7 

    acc = 0
    for name, data in RARITY.items():
        acc += data["chance"]
        if r <= acc:
            return name, data
    return "COMUM", RARITY["COMUM"]

upg_images = {}

# =========================================================
# CLASSES AUXILIARES
# =========================================================
class Button:
    def __init__(self, x_ratio, y_ratio, w, h, text, font, color=(40, 40, 60), subtext="", hover_color=(60, 60, 90), locked=False, lock_req=""):
        self.x_ratio, self.y_ratio = x_ratio, y_ratio
        self.w, self.h = w, h
        self.text, self.font, self.color = text, font, color
        self.subtext = subtext
        self.hover_color, self.is_hovered = hover_color, False
        self.was_hovered = False
        self.rect = pygame.Rect(0, 0, w, h)
        self.locked = locked
        self.lock_req = lock_req
        self.update_rect()

    def update_rect(self):
        cx, cy = int(SCREEN_W * self.x_ratio), int(SCREEN_H * self.y_ratio)
        self.rect.center = (cx, cy)

    def draw(self, screen):
        # Cor diferente se bloqueado
        if self.locked:
            col = (30, 30, 30)
            border_col = (100, 50, 50)
        else:
            col = self.hover_color if self.is_hovered else self.color
            border_col = (0, 255, 255)

        pygame.draw.rect(screen, col, self.rect, border_radius=12)
        pygame.draw.rect(screen, border_col, self.rect, 3, border_radius=12)
        
        # Texto
        alpha = 100 if self.locked else 255
        txt = self.font.render(self.text, True, (255, 255, 255))
        txt.set_alpha(alpha)
        screen.blit(txt, txt.get_rect(center=(self.rect.centerx, self.rect.centery - (10 if self.subtext or self.locked else 0))))
        
        if self.locked:
            # Desenha ícone de cadeado ou texto
            lock_txt = pygame.font.SysFont("Arial", 16, bold=True).render(f"BLOQUEADO: {self.lock_req}", True, (255, 100, 100))
            screen.blit(lock_txt, lock_txt.get_rect(center=(self.rect.centerx, self.rect.centery + 15)))
        elif self.subtext:
            stxt = pygame.font.SysFont("Arial", 16).render(self.subtext, True, (200, 200, 200))
            screen.blit(stxt, stxt.get_rect(center=(self.rect.centerx, self.rect.centery + 15)))

    def check_hover(self, m_pos, hover_sound=None):
        self.is_hovered = self.rect.collidepoint(m_pos)
        if self.is_hovered and not self.was_hovered:
            if hover_sound and not self.locked: hover_sound.play()
        self.was_hovered = self.is_hovered
        return self.is_hovered and not self.locked

class AssetLoader:
    def __init__(self):
        if not os.path.exists(ASSET_DIR): 
            print(f"[ASSETS] Criando pasta: {ASSET_DIR}")
            os.makedirs(ASSET_DIR)
        else:
            print(f"[ASSETS] Pasta encontrada: {os.path.abspath(ASSET_DIR)}")
    
    def load_image(self, name, size=None, fallback_colors=((200,200,200), (100,100,100))):
        # Tenta carregar com extensão .png e .jpg para flexibilidade
        for ext in [".png", ".jpg", ".jpeg"]:
            path = os.path.join(ASSET_DIR, f"{name}{ext}")
            if os.path.exists(path):
                try:
                    img = pygame.image.load(path).convert_alpha()
                    if size: img = pygame.transform.scale(img, size)
                    print(f"[ASSETS] Sucesso: {name}{ext}")
                    return img
                except Exception as e:
                    print(f"[ASSETS] Erro ao carregar {name}{ext}: {e}")
        
        # Se falhar, usa o fallback colorido
        print(f"[ASSETS] Falha ao localizar {name}.png - Usando Fallback")
        w, h = size if size else (64, 64)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        if len(fallback_colors[0]) == 4: # Suporte a Alpha no fallback
            s.fill(fallback_colors[0])
        else:
            pygame.draw.rect(s, fallback_colors[0], (0, 0, w, h), border_radius=min(w,h)//4)
        pygame.draw.rect(s, fallback_colors[1], (0, 0, w, h), width=2, border_radius=min(w,h)//4)
        return s

    def load_animation(self, base_name, count, size, fallback_colors=((200,200,200), (100,100,100))):
        frames = []
        # Tenta primeiro carregar a sequência (nome_0, nome_1, ...)
        # Se não encontrar NENHUM frame da sequência, tenta carregar o nome base como frame único
        sequence_found = False
        for i in range(count):
            img_name = f"{base_name}_{i}"
            path_check = os.path.join(ASSET_DIR, f"{img_name}.png")
            if os.path.exists(path_check):
                sequence_found = True
                break
        
        if sequence_found:
            for i in range(count):
                frames.append(self.load_image(f"{base_name}_{i}", size, fallback_colors))
        else:
            # Fallback para imagem única repetida (para animações onde o usuário só tem 1 frame)
            img = self.load_image(base_name, size, fallback_colors)
            for _ in range(count):
                frames.append(img.copy())
        return frames
    
    def load_sound(self, name, volume=None):
        for ext in [".wav", ".mp3", ".ogg"]:
            path = os.path.join(ASSET_DIR, name + ext)
            if os.path.exists(path):
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.set_volume(volume if volume is not None else SFX_VOLUME)
                    return snd
                except: continue
        return None

    def play_music(self, name, loop=-1):
        for ext in [".mp3", ".wav", ".ogg"]:
            path = os.path.join(ASSET_DIR, name + ext)
            if os.path.exists(path):
                try:
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(MUSIC_VOLUME)
                    pygame.mixer.music.play(loop)
                    return
                except: continue

# =========================================================
# ENTIDADES
# =========================================================

class Drop(pygame.sprite.Sprite):
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

class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, color, size, speed, life):
        super().__init__()
        self.color = color
        self.original_size = size
        self.size = size
        self.life = life
        self.max_life = life
        self.image = pygame.Surface((int(size), int(size)))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        angle = random.uniform(0, 360)
        rad = math.radians(angle)
        speed_var = random.uniform(speed * 0.5, speed * 1.5)
        self.vel = pygame.Vector2(math.cos(rad), math.sin(rad)) * speed_var

    def update(self, dt, cam):
        self.pos += self.vel * dt
        self.vel *= 0.92  
        self.life -= dt
        if self.life <= 0:
            self.kill()
        else:
            # Otimização: Reduzir frequência de redimensionamento
            if int(self.life * 10) != int((self.life + dt) * 10):
                ratio = self.life / self.max_life
                new_size = max(1, int(self.original_size * ratio))
                if new_size != self.size:
                    self.size = new_size
                    self.image = pygame.transform.scale(self.image, (new_size, new_size))
        self.rect.center = self.pos + cam

class DamageText(pygame.sprite.Sprite):
    def __init__(self, pos, amount, is_crit=False, color=(255, 255, 255)):
        super().__init__()
        size = 36 if is_crit else 22
        final_color = (255, 215, 0) if is_crit else color
        text_content = f"{amount}!" if is_crit else str(amount)
        
        font = pygame.font.SysFont("Arial", size, bold=True)
        self.image = font.render(text_content, True, final_color)
        
        if is_crit:
            base_surf = pygame.Surface((self.image.get_width() + 4, self.image.get_height() + 4), pygame.SRCALPHA)
            outline = font.render(text_content, True, (0, 0, 0))
            base_surf.blit(outline, (0, 0)); base_surf.blit(outline, (2, 0)); base_surf.blit(outline, (0, 2)); base_surf.blit(outline, (2, 2))
            base_surf.blit(self.image, (1, 1))
            self.image = base_surf

        self.rect = self.image.get_rect()
        offset_x = random.randint(-20, 20)
        offset_y = random.randint(-20, 20)
        self.world_pos = pygame.Vector2(pos.x + offset_x, pos.y + offset_y)
        self.vel_y = -150 if is_crit else -80 
        self.timer = 0.8 if is_crit else 0.6  
        self.alpha = 255

    def update(self, dt, cam):
        self.world_pos.y += self.vel_y * dt
        self.timer -= dt
        if self.timer <= 0:
            self.kill()
        else:
            self.alpha = int((self.timer / 0.6) * 255)
        self.rect.center = self.world_pos + cam

class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, vel, dmg, frames):
        super().__init__()
        self.anim_frames = frames 
        self.frame_idx = 0
        self.anim_timer = 0
        self.image = self.anim_frames[0]
        self.rect = self.image.get_rect()
        self.hitbox = self.rect.inflate(-max(4, self.rect.width // 6), -max(4, self.rect.height // 6))
        self.pos, self.vel, self.dmg = pygame.Vector2(pos.x, pos.y), vel, dmg
        self.pierce, self.hit_enemies = PROJ_PIERCE, []
        self.ricochet = PROJ_RICOCHET
        self.is_melee = False

    def update(self, dt, cam):
        self.pos += self.vel * dt
        self.anim_timer += dt
        if self.anim_timer > 0.05:
            self.anim_timer = 0
            self.frame_idx = (self.frame_idx + 1) % len(self.anim_frames)
            self.image = self.anim_frames[self.frame_idx]
        self.rect.center = self.pos + cam
        self.hitbox = self.rect.inflate(-max(4, self.rect.width // 6), -max(4, self.rect.height // 6))
        self.hitbox.center = self.rect.center
        if not pygame.Rect(-1000,-1000,SCREEN_W+2000,SCREEN_H+2000).collidepoint(self.rect.center): self.kill()

class MeleeSlash(pygame.sprite.Sprite):
    def __init__(self, player, target_dir, dmg, frames):
        super().__init__()
        self.anim_frames = frames
        self.frame_idx = 0
        self.anim_timer = 0
        self.player = player
        self.target_dir = target_dir.normalize() if target_dir.length() > 0 else pygame.Vector2(1, 0)
        self.distance = 90  
        self.is_melee = True 
        shoot_angle = math.degrees(math.atan2(-self.target_dir.y, self.target_dir.x))
        self.anim_frames = [pygame.transform.rotate(f, shoot_angle) for f in frames]
        self.image = self.anim_frames[0]
        self.rect = self.image.get_rect()
        self.pos = self.player.pos + (self.target_dir * self.distance)
        self.dmg = dmg
        self.hit_enemies = []

    def update(self, dt, cam):
        self.anim_timer += dt
        if self.anim_timer > 0.04:  
            self.anim_timer = 0
            self.frame_idx += 1
            if self.frame_idx >= len(self.anim_frames):
                self.kill(); return
            self.image = self.anim_frames[self.frame_idx]
        self.pos = self.player.pos + (self.target_dir * self.distance)
        self.rect.center = self.pos + cam

class EnemyProjectile(pygame.sprite.Sprite):
    def __init__(self, pos, vel, dmg, loader, img_name):
        super().__init__()
        base_frames = loader.load_animation(img_name, 4, (36, 36), fallback_colors=((255, 120, 0), (200, 50, 0)))
        shoot_angle = math.degrees(math.atan2(-vel.y, vel.x))
        self.anim_frames = [pygame.transform.rotate(f, shoot_angle) for f in base_frames]
        self.frame_idx = 0
        self.anim_timer = 0
        self.image = self.anim_frames[0]
        self.rect = self.image.get_rect()
        self.pos = pygame.Vector2(pos.x, pos.y)
        self.vel = vel
        self.dmg = dmg

    def update(self, dt, cam):
        self.pos += self.vel * dt
        self.anim_timer += dt
        if self.anim_timer > 0.05:
            self.anim_timer = 0
            self.frame_idx = (self.frame_idx + 1) % len(self.anim_frames)
            self.image = self.anim_frames[self.frame_idx]
        self.rect.center = self.pos + cam
        if not pygame.Rect(-1000,-1000,SCREEN_W+2000,SCREEN_H+2000).collidepoint(self.rect.center): self.kill()

class Puddle(pygame.sprite.Sprite):
    def __init__(self, pos, loader):
        super().__init__()
        self.image = loader.load_image("puddle_black", (80, 80), ((20, 0, 20), (0, 0, 0)))
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.Vector2(pos)
        self.timer = 4.0 
        self.tick_timer = 0.0
        self.hitbox = self.rect.inflate(-20, -20)

    def update(self, dt, cam):
        self.timer -= dt
        if self.timer <= 0:
            self.kill()
        self.rect.center = self.pos + cam
        self.hitbox.center = self.pos

#quantidade de imagens para cada personagem e tamanho dos personagens (para carregar animações corretamente)
class Player(pygame.sprite.Sprite):
    def __init__(self, loader, char_id):
        super().__init__()
        self.char_id = char_id  
        data = CHAR_DATA[char_id]
        char_size = data.get("size", (180, 180))
        self.anim_frames = loader.load_animation(f"char{char_id}", 12, char_size)
        self.flipped_frames = [pygame.transform.flip(f, True, False) for f in self.anim_frames]
        self.frame_idx = 0
        self.anim_timer = 0.0
        self.facing_right = True
        self.image = self.anim_frames[0]
        self.rect = self.image.get_rect()
        self.pos = pygame.Vector2(0, 0)
        
        self.dash_active = False
        self.dash_timer = 0.0
        self.dash_cooldown_timer = 0.0
        
        self.ult_charge = 0
        self.ult_max = ULTIMATE_MAX_CHARGE
        self.ult_active_timer = 0.0 
        self.ult_active = False
        
        self.hp, self.iframes = PLAYER_MAX_HP, 0.0

    def start_dash(self, particles_group):
        if self.dash_cooldown_timer <= 0:
            self.dash_active = True
            self.dash_timer = DASH_DURATION
            self.dash_cooldown_timer = DASH_COOLDOWN
            self.iframes = DASH_DURATION + 0.1 
            return True
        return False

    def update(self, dt, keys, obstacles, particles_group, biome_type="normal"):
        if not hasattr(self, "vel"): self.vel = pygame.Vector2(0, 0)
        
        self.vel = pygame.Vector2(0, 0)

        if self.dash_active:
            self.dash_timer -= dt
            if random.random() < 0.5:
                particles_group.add(Particle(self.pos, (200, 200, 200), 5, 50, 0.3))
                
            if self.dash_timer <= 0:
                self.dash_active = False
        
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt
            
        if self.ult_active_timer > 0:
            self.ult_active_timer -= dt
            if self.ult_active_timer <= 0:
                self.ult_active = False

        m = pygame.Vector2(0, 0)
        if is_control_pressed(keys, "up"): m.y -= 1
        if is_control_pressed(keys, "down"): m.y += 1
        if is_control_pressed(keys, "left"): m.x -= 1
        if is_control_pressed(keys, "right"): m.x += 1
        
        moving = m.length_squared() > 0
        if moving:
            current_speed = DASH_SPEED if self.dash_active else PLAYER_SPEED
            target_vel = m.normalize() * current_speed
            
            self.vel = target_vel
            
            if m.x > 0: self.facing_right = True
            elif m.x < 0: self.facing_right = False
            
            move = self.vel * dt
            self.pos.x += move.x
            for obs in obstacles:
                if obs.hitbox.collidepoint(self.pos): self.pos.x -= move.x
            self.pos.y += move.y
            for obs in obstacles:
                if obs.hitbox.collidepoint(self.pos): self.pos.y -= move.y
            
            self.anim_timer += dt
            if self.anim_timer > 0.08:
                self.anim_timer = 0
                self.frame_idx = (self.frame_idx + 1) % len(self.anim_frames)
        else:
            self.frame_idx = 0

        self.image = self.anim_frames[self.frame_idx] if self.facing_right else self.flipped_frames[self.frame_idx]
        self.iframes = max(0, self.iframes - dt)
        self.rect.center = (SCREEN_W//2, SCREEN_H//2)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, kind, pos, loader, diff_mults, time_scale=1.0, boss_tier=1, is_elite=False): 
        super().__init__()
        self.kind = kind
        self.is_elite = is_elite
        
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
        else: # Runner
            color = ((255, 100, 100), (150, 0, 0))
            size = (100, 100)
            frames = 11

        self.anim_frames = loader.load_animation(kind, frames, size, fallback_colors=color)
        self.flipped_frames = [pygame.transform.flip(f, True, False) for f in self.anim_frames]
        
        self.white_frames = []
        for frame in self.anim_frames:
            mask = pygame.mask.from_surface(frame)
            white_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0,0,0,0))
            self.white_frames.append(white_surf)
        self.flipped_white_frames = [pygame.transform.flip(f, True, False) for f in self.white_frames]
        
        self.frozen_frames = []
        for frame in self.anim_frames:
            mask = pygame.mask.from_surface(frame)
            blue_surf = mask.to_surface(setcolor=(0, 255, 255, 150), unsetcolor=(0,0,0,0))
            combined = frame.copy()
            combined.blit(blue_surf, (0,0), special_flags=pygame.BLEND_RGBA_ADD)
            self.frozen_frames.append(combined)
        self.flipped_frozen_frames = [pygame.transform.flip(f, True, False) for f in self.frozen_frames]
        
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
            "boss": (BOSS_MAX_HP, 95),
            "slime": (5, 110), 
            "robot": (8, 130)  
        }
        base_hp, base_spd = stats[kind]
        
        if kind == "robot": self.shot_cooldown = 1.0 
        
        if kind == "boss":
            self.hp = base_hp * diff_mults["hp_mult"] * time_scale * boss_tier
        else:
            self.hp = base_hp * diff_mults["hp_mult"] * time_scale
            
        self.speed = base_spd * diff_mults["spd_mult"] * min(1.5, time_scale) 
        self.max_hp = self.hp

    def update(self, dt, p_pos, cam, obstacles, enemy_projectiles, puddles, loader, selected_pact="NENHUM"): 
        self.pos += self.knockback
        self.knockback *= 0.85 
        
        if self.flash_timer > 0: self.flash_timer -= dt
        
        if self.frozen_timer > 0:
            self.frozen_timer -= dt
            current_set = self.frozen_frames if self.facing_right else self.flipped_frozen_frames
            self.image = current_set[self.frame_idx] 
            self.rect.center = self.pos + cam
            return 

        d = (p_pos - self.pos)
        dist = d.length()
        
        can_move = self.knockback.length() < 3.0
        
        if dist > 0 and can_move:
            is_ranged_unit = (self.kind == "shooter" or self.kind == "robot")
            stop_dist = 450 if self.kind == "shooter" else 300 
            if is_ranged_unit and dist < stop_dist:
                move = pygame.Vector2(0, 0)
            else:
                # Lógica de Fases do Boss
                move_speed = self.speed
                
                # Pacto de Velocidade
                if selected_pact == "VELOCIDADE":
                    move_speed *= 1.5

                if self.kind == "boss":
                    if self.hp < self.max_hp * 0.25: # Fase 3: Fúria Total
                        move_speed *= 2.0
                    elif self.hp < self.max_hp * 0.5: # Fase 2: Agitado
                        move_speed *= 1.5
                
                move = (d / dist) * move_speed * dt
            
            if d.x > 0: self.facing_right = True
            elif d.x < 0: self.facing_right = False
            
            if move.length_squared() > 0:
                self.pos += move
                if self.kind != "boss":
                    for obs in obstacles:
                        if obs.hitbox.collidepoint(self.pos): self.pos -= move
            
            anim_speed = 0.15 if self.kind == "boss" else 0.1
            self.anim_timer += dt
            if self.anim_timer > anim_speed:
                self.anim_timer = 0
                self.frame_idx = (self.frame_idx + 1) % len(self.anim_frames)
        
        if self.kind == "shooter" or self.kind == "robot" or self.kind == "boss":
            self.shot_timer += dt
            
            # Cooldown dinâmico para o Boss baseado na vida
            current_cooldown = self.shot_cooldown
            if self.kind == "boss":
                if self.hp < self.max_hp * 0.25: current_cooldown *= 0.4
                elif self.hp < self.max_hp * 0.5: current_cooldown *= 0.7

            if self.shot_timer >= current_cooldown:
                self.shot_timer = 0.0
                
                if self.kind == "boss":
                    # Padrões de tiro do Boss
                    num_shots = 8
                    if self.hp < self.max_hp * 0.25: num_shots = 16
                    elif self.hp < self.max_hp * 0.5: num_shots = 12
                    
                    for i in range(num_shots):
                        angle = (360 / num_shots) * i
                        vel = pygame.Vector2(1, 0).rotate(angle) * 350.0
                        enemy_projectiles.add(EnemyProjectile(self.pos, vel, 1.0, loader, SHOOTER_PROJ_IMAGE))
                else:
                    range_limit = 500 if self.kind == "shooter" else 450
                    if 0 < dist < range_limit:
                        speed_proj = 300.0 if self.kind == "shooter" else 150.0 
                        vel = (d / dist) * speed_proj 
                        enemy_projectiles.add(EnemyProjectile(self.pos, vel, 0.5, loader, SHOOTER_PROJ_IMAGE))
        
        if self.kind == "slime":
            self.puddle_timer += dt
            if self.puddle_timer >= 2.5: 
                self.puddle_timer = 0.0
                puddles.add(Puddle(self.pos, loader))

        if self.flash_timer > 0:
            current_set = self.white_frames if self.facing_right else self.flipped_white_frames
        else:
            current_set = self.anim_frames if self.facing_right else self.flipped_frames
            
        self.image = current_set[self.frame_idx]
        
        if self.is_elite:
            # Aura dourada para Elites
            aura_surf = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            pygame.draw.ellipse(aura_surf, (255, 215, 0, 100), aura_surf.get_rect(), 3)
            self.image = self.image.copy()
            self.image.blit(aura_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

        self.rect.center = self.pos + cam

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, pos, loader, kind):
        super().__init__()
        sizes = [(90, 90), (70, 90), (100, 100), (100, 90)]
        self.image = loader.load_image(f"obstacle_{kind}", sizes[kind], ((80,80,80),(40,40,40)))
        self.rect, self.pos = self.image.get_rect(), pos
        self.hitbox = pygame.Rect(0, 0, sizes[kind][0]-20, sizes[kind][1]-20)
    def update(self, dt, cam):
        self.rect.center = self.pos + cam
        self.hitbox.center = self.pos

class Gem(pygame.sprite.Sprite):
    def __init__(self, pos, loader):
        super().__init__()
        self.image = loader.load_image("gem", (24, 24), ((0,255,255), (255,255,255)))
        self.rect, self.pos = self.image.get_rect(), pos
        self.fpos = pygame.Vector2(pos)
        self.magnetic = False 

    def update(self, dt, cam, player_pos=None):
        if self.magnetic and player_pos:
            d = player_pos - self.fpos
            if d.length_squared() > 0:
                move = d.normalize() * 900 * dt
                self.fpos += move
        
        self.rect.center = self.fpos + cam

# =========================================================
# FUNÇÕES AUXILIARES DO JOGO
# =========================================================

# Referências globais que serão preenchidas em main()
player = None
enemies = None
projectiles = None
enemy_projectiles = None
gems = None
drops = None
particles = None
obstacles = None
puddles = None
damage_texts = None
loader = None
SFX = {}
snd_hover = None
snd_click = None
upg_images = {}
menu_char_anims = []
screen = None

# Variáveis de estado de jogo (inicializadas em reset_game)
kills = 0
game_time = 0.0
level = 1
xp = 0
shot_t = 0.0
aura_t = 0.0
aura_anim_timer = 0.0
aura_frame_idx = 0
orb_rot_angle = 0.0
spawn_t = 0.0
bosses_spawned = 0
session_boss_kills = 0
session_max_level = 1
triggered_hordes = set()
player_upgrades = []
has_bazuca = False
has_buraco_negro = False
has_serras = False
has_tesla = False
has_ceifador = False
has_berserk = False
chest_loot = []
chest_ui_timer = 0.0
new_unlocks_this_session = []
selected_difficulty = "MÉDIO"
selected_pact = "NENHUM"
selected_bg = "dungeon"
current_bg_name = "bg_dungeon"
up_options = []
up_keys = []
up_rarities = []
active_explosions = []

# Assets de jogo (preenchidos em load_all_assets)
ground_img = None
menu_bg_img = None
aura_frames = []
explosion_frames_raw = []
projectile_frames_raw = []
slash_frames_raw = []
orb_img = None
tornado_img = None


class ExplosionAnimation:
    def __init__(self, pos, radius, raw_frames, frame_duration_ms=70):
        self.pos = pygame.Vector2(pos)
        self.radius = int(radius)
        self.frame_duration_ms = frame_duration_ms
        self.start_ms = pygame.time.get_ticks()
        self.frame_idx = 0
        size = (self.radius * 2, self.radius * 2)
        self.frames = [pygame.transform.scale(f, size) for f in raw_frames]
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, now_ms):
        elapsed = max(0, now_ms - self.start_ms)
        self.frame_idx = elapsed // self.frame_duration_ms
        if self.frame_idx >= len(self.frames):
            return False
        self.image = self.frames[self.frame_idx]
        self.rect = self.image.get_rect(center=self.pos)
        return True

    def draw(self, screen, cam):
        draw_rect = self.image.get_rect(center=self.pos + cam)
        screen.blit(self.image, draw_rect, special_flags=pygame.BLEND_RGBA_ADD)


def load_explosion_frames(loader, size=(128, 128)):
    frames = []
    for i in range(6):
        img_name = f"explosion_{i}"
        img_path = os.path.join(ASSET_DIR, f"{img_name}.png")
        if os.path.exists(img_path):
            frames.append(loader.load_image(img_name, size, ((255, 150, 0, 200), (255, 50, 0, 150))))

    if len(frames) == 6:
        return frames

    return loader.load_animation("explosion", 6, size, fallback_colors=((255, 150, 0, 200), (255, 50, 0, 150)))


def projectile_enemy_collision(projectile, enemy):
    p_rect = getattr(projectile, "hitbox", projectile.rect)
    return p_rect.colliderect(enemy.rect)


def play_sfx(name):
    """Reproduz um efeito sonoro pelo nome, se disponível."""
    global SFX, settings
    if settings and settings["audio"].get("mute") == "On":
        return
    snd = SFX.get(name)
    if snd:
        vol = settings["audio"].get("sfx", 100) / 100.0 if settings else 1.0
        snd.set_volume(vol)
        snd.play()


def pick_upgrades_with_synergy(pool, current_upgrades, k=3):
    """Seleciona upgrades com lógica de sinergia e evoluções."""
    available = [u for u in pool if u in save_data["unlocks"] or u in DEFAULT_UNLOCKS]
    
    # Adiciona evoluções se os pré-requisitos forem atendidos
    for evo_name, evo_data in EVOLUTIONS.items():
        if (evo_data["base"] in current_upgrades and
            evo_data["passive"] in current_upgrades and
            evo_name not in current_upgrades and
            evo_name not in available):
            available.append(evo_name)
    
    # Remove upgrades já no máximo (simplificado)
    filtered = [u for u in available if u not in current_upgrades or
                current_upgrades.count(u) < MAX_UPGRADE_LEVEL]
    
    if not filtered:
        filtered = list(pool)
    
    k = min(k, len(filtered))
    
    # Prioriza sinergias
    synergy_picks = []
    for u in filtered:
        tags = UPGRADE_TAGS.get(u, set())
        for existing in current_upgrades:
            existing_tags = UPGRADE_TAGS.get(existing, set())
            if tags & existing_tags:
                synergy_picks.append(u)
                break
    
    result = []
    if synergy_picks:
        result.append(random.choice(synergy_picks))
    
    remaining = [u for u in filtered if u not in result]
    random.shuffle(remaining)
    result.extend(remaining[:k - len(result)])
    
    return result[:k]


def apply_upgrade(key, mult=1.0):
    """Aplica um upgrade ao jogador, modificando as variáveis globais."""
    global PLAYER_MAX_HP, PROJECTILE_DMG, SHOT_COOLDOWN, PLAYER_SPEED
    global PROJECTILE_SPEED, PICKUP_RANGE, AURA_DMG, AURA_RANGE
    global PROJ_COUNT, PROJ_PIERCE, EXPLOSION_RADIUS, ORB_COUNT
    global CRIT_CHANCE, EXECUTE_THRESH, HAS_FURY, player, player_upgrades
    global has_bazuca, has_buraco_negro, has_serras, has_tesla, has_ceifador, has_berserk
    global PROJ_RICOCHET
    
    player_upgrades.append(key)
    
    # Evoluções
    if key == "BAZUCA":
        has_bazuca = True; return
    elif key == "BURACO NEGRO":
        has_buraco_negro = True; return
    elif key == "SERRAS MÁGICAS":
        has_serras = True; return
    elif key == "TESLA":
        has_tesla = True; return
    elif key == "CEIFADOR":
        has_ceifador = True; return
    elif key == "BERSERK":
        has_berserk = True; return
    
    if key == "DANO ++":         PROJECTILE_DMG += int(2 * mult)
    elif key == "VELOCIDADE ++": PLAYER_SPEED = min(600, PLAYER_SPEED * (1 + 0.15 * mult))
    elif key == "TIRO RÁPIDO":   SHOT_COOLDOWN = max(0.05, SHOT_COOLDOWN * (1 - 0.15 * mult))
    elif key == "VIDA MÁXIMA":
        PLAYER_MAX_HP += int(2 * mult)
        if player: player.hp = min(player.hp + int(2 * mult), PLAYER_MAX_HP)
    elif key == "AURA MÁGICA":   AURA_DMG = max(AURA_DMG, 1); AURA_DMG += int(1 * mult)
    elif key == "ÍMÃ DE XP":      PICKUP_RANGE = min(600, PICKUP_RANGE + 80 * mult)
    elif key == "TIRO MÚLTIPLO": PROJ_COUNT = min(8, PROJ_COUNT + 1)
    elif key == "EXPLOSÃO":      EXPLOSION_RADIUS = max(EXPLOSION_RADIUS, 80); EXPLOSION_RADIUS += int(40 * mult)
    elif key == "PERFURAÇÃO":    PROJ_PIERCE += 1
    elif key == "ORBES MÁGICOS": ORB_COUNT = min(6, ORB_COUNT + 1)
    elif key == "SORTE":         CRIT_CHANCE = min(0.95, CRIT_CHANCE + 0.10 * mult)
    elif key == "CURA":
        if player: player.hp = min(PLAYER_MAX_HP, player.hp + PLAYER_MAX_HP)
    elif key == "RICOCHE":       PROJ_RICOCHET += 1
    elif key == "EXECUÇÃO":      EXECUTE_THRESH = min(0.30, EXECUTE_THRESH + 0.12 * mult)
    elif key == "FÚRIA":         HAS_FURY = True
    elif key == "CAPA INVISÍVEL": pass  # Efeito passivo tratado no Enemy.update
    elif key == "LUVA EXPULSÃO": pass  # Efeito passivo tratado no knockback
    elif key == "TREVO SORTE":   pass  # Efeito passivo em roll_rarity


def check_achievements(stats_override=None, save_when_unlocked=False):
    """Verifica e desbloqueia conquistas com base nas estatísticas."""
    global new_unlocks_this_session
    stats = stats_override if stats_override is not None else save_data["stats"]
    unlocked_any = False
    for ach_id, ach_data in ACHIEVEMENTS.items():
        if ach_id not in save_data["unlocks"]:
            try:
                if ach_data["req"](stats):
                    save_data["unlocks"].append(ach_id)
                    new_unlocks_this_session.append(ach_data["name"])
                    if SFX.get("unlock"): SFX["unlock"].play()
                    unlocked_any = True
            except Exception:
                pass

    if unlocked_any and save_when_unlocked:
        save_game()
    return unlocked_any


def load_all_assets():
    """Carrega (ou recarrega) todos os assets gráficos e de áudio do jogo."""
    global ground_img, menu_bg_img, aura_frames, explosion_frames_raw
    global projectile_frames_raw, slash_frames_raw, orb_img, tornado_img
    global upg_images, menu_char_anims, loader, current_bg_name
    
    bg_name = BG_DATA.get(selected_bg, BG_DATA["dungeon"])["name"]
    current_bg_name = bg_name
    
    ground_img = loader.load_image(bg_name, (256, 256), ((20, 20, 30), (10, 10, 20)))
    menu_bg_img = loader.load_image("menu_bg", (SCREEN_W, SCREEN_H), ((10, 5, 20), (5, 0, 10)))
    
    aura_frames = loader.load_animation("aura", 4, (400, 400), fallback_colors=((100, 0, 200, 80), (80, 0, 160, 60)))
    explosion_frames_raw = load_explosion_frames(loader, (128, 128))
    projectile_frames_raw = loader.load_animation("projectile", 4, (40, 20), fallback_colors=((255, 255, 100), (200, 200, 0)))
    slash_frames_raw = loader.load_animation("slash", 6, (120, 120), fallback_colors=((255, 255, 200, 180), (200, 200, 150, 120)))
    orb_img = loader.load_image("orb", (50, 50), ((0, 200, 255), (0, 100, 200)))
    tornado_img = loader.load_image("tornado", (300, 300), ((200, 200, 255, 150), (150, 150, 200, 100)))
    
    # Ícones de upgrades
    for upg_key, icon_name in UPGRADE_ICONS.items():
        upg_images[upg_key] = loader.load_image(icon_name, (64, 64))
    
    # assets de personagens
    # Animações dos personagens para o menu
    menu_char_anims = []
    for char_id, char_data in CHAR_DATA.items():
        menu_size = char_data.get("menu_size", (200, 200))
        frames = loader.load_animation(f"char{char_id}", 10, menu_size)
        menu_char_anims.append(frames)
    
    # Música do bioma
    music_name = BG_DATA.get(selected_bg, BG_DATA["dungeon"])["music"]
    loader.play_music(music_name)


def reset_game(char_id=0):
    """Reinicia todas as variáveis de estado para uma nova partida."""
    global player, enemies, projectiles, enemy_projectiles, gems, drops
    global particles, obstacles, puddles, damage_texts, active_explosions
    global kills, game_time, level, xp, shot_t, aura_t, aura_anim_timer
    global aura_frame_idx, orb_rot_angle, spawn_t, bosses_spawned
    global session_boss_kills, session_max_level, triggered_hordes
    global player_upgrades, has_bazuca, has_buraco_negro, has_serras
    global has_tesla, has_ceifador, has_berserk, chest_loot, chest_ui_timer
    global new_unlocks_this_session, up_options, up_keys, up_rarities
    global PLAYER_MAX_HP, PROJECTILE_DMG, SHOT_COOLDOWN, PLAYER_SPEED
    global PROJECTILE_SPEED, PICKUP_RANGE, AURA_DMG, PROJ_COUNT, PROJ_PIERCE
    global EXPLOSION_RADIUS, ORB_COUNT, CRIT_CHANCE, EXECUTE_THRESH, HAS_FURY
    global CRIT_DMG_MULT, EXPLOSION_SIZE_MULT, REGEN_RATE, DAMAGE_RES
    global THORNS_PERCENT, FIRE_DMG_MULT, BURN_AURA_MULT, HAS_CHAOS_BOLT, HAS_INFERNO
    global PROJ_RICOCHET
    
    save_data["stats"]["games_played"] += 1
    
    # Resetar stats base
    char_data = CHAR_DATA[char_id]
    PLAYER_MAX_HP = char_data["hp"]
    PLAYER_SPEED = char_data["speed"]
    PROJECTILE_DMG = 2
    SHOT_COOLDOWN = 0.35
    PROJECTILE_SPEED = 560.0
    PICKUP_RANGE = 50.0
    AURA_DMG = 0
    PROJ_COUNT = 1
    PROJ_PIERCE = 0
    PROJ_RICOCHET = 0
    EXPLOSION_RADIUS = 0
    ORB_COUNT = 0
    CRIT_CHANCE = 0.05
    EXECUTE_THRESH = 0.0
    HAS_FURY = False
    
    # Aplicar upgrades permanentes da árvore de talentos
    pu = save_data["perm_upgrades"]
    CRIT_DMG_MULT = 2.0 + pu.get("crit_dmg", 0) * 0.20
    EXPLOSION_SIZE_MULT = 1.0 + pu.get("exp_size", 0) * 0.15
    HAS_CHAOS_BOLT = pu.get("chaos_bolt", 0) >= 1
    REGEN_RATE = pu.get("regen", 0) * 0.1
    DAMAGE_RES = pu.get("aura_res", 0) * 0.10
    THORNS_PERCENT = 0.20 if pu.get("thorns", 0) >= 1 else 0.0
    FIRE_DMG_MULT = 1.0 + pu.get("fire_dmg", 0) * 0.15
    BURN_AURA_MULT = 1.0 + pu.get("burn_area", 0) * 0.20
    HAS_INFERNO = pu.get("inferno", 0) >= 1
    
    # Resetar grupos de sprites
    enemies = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    enemy_projectiles = pygame.sprite.Group()
    gems = pygame.sprite.Group()
    drops = pygame.sprite.Group()
    particles = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()
    puddles = pygame.sprite.Group()
    damage_texts = pygame.sprite.Group()
    
    # Resetar variáveis de estado
    kills = 0
    game_time = 0.0
    level = 1
    xp = 0
    shot_t = 0.0
    aura_t = 0.0
    aura_anim_timer = 0.0
    aura_frame_idx = 0
    orb_rot_angle = 0.0
    spawn_t = 0.0
    bosses_spawned = 0
    session_boss_kills = 0
    session_max_level = 1
    triggered_hordes = set()
    player_upgrades = []
    has_bazuca = False
    has_buraco_negro = False
    has_serras = False
    has_tesla = False
    has_ceifador = False
    has_berserk = False
    chest_loot = []
    chest_ui_timer = 0.0
    new_unlocks_this_session = []
    active_explosions = []
    up_options = []
    up_keys = []
    up_rarities = []
    
    # Criar jogador
    player = Player(loader, char_id)


def clear_current_run_state():
    """Limpa estado transitório da run atual e retorna ao menu sem contar nova partida."""
    global player, enemies, projectiles, enemy_projectiles, gems, drops
    global particles, obstacles, puddles, damage_texts, active_explosions
    global kills, game_time, level, xp, shot_t, aura_t, aura_anim_timer
    global aura_frame_idx, orb_rot_angle, spawn_t, bosses_spawned
    global session_boss_kills, session_max_level, triggered_hordes
    global player_upgrades, chest_loot, chest_ui_timer, up_options, up_keys, up_rarities

    player = None
    enemies = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    enemy_projectiles = pygame.sprite.Group()
    gems = pygame.sprite.Group()
    drops = pygame.sprite.Group()
    particles = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()
    puddles = pygame.sprite.Group()
    damage_texts = pygame.sprite.Group()

    kills = 0
    game_time = 0.0
    level = 1
    xp = 0
    shot_t = 0.0
    aura_t = 0.0
    aura_anim_timer = 0.0
    aura_frame_idx = 0
    orb_rot_angle = 0.0
    spawn_t = 0.0
    bosses_spawned = 0
    session_boss_kills = 0
    session_max_level = 1
    triggered_hordes = set()
    player_upgrades = []
    chest_loot = []
    chest_ui_timer = 0.0
    active_explosions = []
    up_options = []
    up_keys = []
    up_rarities = []


# =========================================================
# LÓGICA PRINCIPAL
# =========================================================

def main():
    # Inicialização do Pygame e Mixer (Deve vir antes de apply_settings para o mixer funcionar)
    pygame.init()
    pygame.mixer.init()
    settings_category = "video"  # ou "audio" ou "controls"

    global settings
    settings = load_settings()
    apply_settings(settings)

    # Globais que serão modificados
    global screen, loader, snd_hover, snd_click, SFX, upg_images, menu_char_anims
    global PLAYER_MAX_HP, PROJECTILE_DMG, SHOT_COOLDOWN, PLAYER_SPEED, PROJECTILE_SPEED, PICKUP_RANGE, AURA_DMG, PROJ_COUNT, PROJ_PIERCE, EXPLOSION_RADIUS, ORB_COUNT, CRIT_CHANCE, EXECUTE_THRESH, HAS_FURY
    global CRIT_DMG_MULT, EXPLOSION_SIZE_MULT, REGEN_RATE, DAMAGE_RES, THORNS_PERCENT, FIRE_DMG_MULT, BURN_AURA_MULT, HAS_CHAOS_BOLT, HAS_INFERNO
    global selected_difficulty, selected_pact, selected_bg, current_bg_name, bg_choices
    global player, enemies, projectiles, enemy_projectiles, gems, drops, particles, obstacles, puddles, damage_texts
    global kills, game_time, level, xp, shot_t, aura_t, aura_anim_timer, aura_frame_idx, orb_rot_angle
    global spawn_t, bosses_spawned, session_boss_kills, session_max_level, triggered_hordes
    global player_upgrades, has_bazuca, has_buraco_negro, has_serras, has_tesla, has_ceifador, has_berserk
    global chest_loot, chest_ui_timer, new_unlocks_this_session, up_options, up_keys, up_rarities, active_explosions
    global ground_img, menu_bg_img, aura_frames, explosion_frames_raw, projectile_frames_raw, slash_frames_raw, orb_img, tornado_img
    global PROJ_RICOCHET, temp_settings, settings_control_waiting, settings_dragging_slider

    # Configuração da tela (Já feita no apply_settings, mas garantindo o caption)
    pygame.display.set_caption("Sobrevivente do Caos")
    clock = pygame.time.Clock()

    # Carregador de assets e sons
    loader = AssetLoader()
    snd_hover, snd_click = loader.load_sound("hover", 0.3), loader.load_sound("click", 0.6)
    SFX = {
        "shoot": loader.load_sound("sfx_shoot"),
        "slash": loader.load_sound("sfx_slash"),
        "hit": loader.load_sound("sfx_hit", 0.4),
        "hurt": loader.load_sound("sfx_hurt"),
        "dash": loader.load_sound("sfx_dash"),
        "gem": loader.load_sound("sfx_gem", 0.3),
        "drop": loader.load_sound("sfx_drop"),
        "levelup": loader.load_sound("sfx_levelup"),
        "explosion": loader.load_sound("sfx_explosion"),
        "ult": loader.load_sound("sfx_ult"),
        "win": loader.load_sound("sfx_win"),
        "lose": loader.load_sound("sfx_lose"),
        "unlock": loader.load_sound("sfx_levelup")
    }

    # Fontes
    font_s = pygame.font.SysFont("Arial", 24, bold=True)
    font_m = pygame.font.SysFont("Arial", 40, bold=True)
    font_l = pygame.font.SysFont("Arial", 80, bold=True)

    # Inicializar botões de configurações (precisam das fontes)
    init_settings_buttons(font_m)

    # Carregar todos os assets gráficos
    load_all_assets()

    # Criar todos os botões da interface
    # Menu reposicionado para o canto inferior esquerdo conforme imagem
    menu_btns = [
        Button(0.15, 0.52, 350, 52, "JOGAR",         font_m),
        Button(0.15, 0.59, 350, 52, "MISSÕES",       font_m),
        Button(0.15, 0.66, 350, 52, "TALENTOS",      font_m),
        Button(0.15, 0.73, 350, 52, "SAVES",         font_m),
        Button(0.15, 0.80, 350, 52, "BIOMA",         font_m),
        Button(0.15, 0.87, 350, 52, "CONFIGURAÇÕES", font_m),
        Button(0.15, 0.94, 350, 52, "SAIR",          font_m, color=(80, 30, 30)),
    ]

    saves_slot_btns = [
        Button(0.5, 0.35, 560, 60, "SLOT 1", font_m),
        Button(0.5, 0.47, 560, 60, "SLOT 2", font_m),
        Button(0.5, 0.59, 560, 60, "SLOT 3", font_m),
    ]
    saves_back_btn = Button(0.5, 0.90, 300, 50, "VOLTAR", font_m, color=(80, 30, 30))

    mission_btns = [Button(0.5, 0.90, 300, 50, "VOLTAR", font_m, color=(80, 30, 30))]
    mission_claim_btns = [
        Button(0.75, 0.25 + i * 0.12, 200, 45, "COLETAR", font_m, color=(40, 100, 40))
        for i in range(3)
    ]

    shop_back_btn = Button(0.5, 0.93, 300, 50, "VOLTAR", font_m, color=(80, 30, 30))
    shop_talent_btns = []
    path_names = list(TALENT_TREE.keys())
    for p_idx, p_name in enumerate(path_names):
        path = TALENT_TREE[p_name]
        skill_keys = list(path["skills"].keys())
        for s_idx, s_key in enumerate(skill_keys):
            bx = 0.75
            by = 0.22 + p_idx * 0.22 + 0.08 + s_idx * 0.045
            shop_talent_btns.append((p_name, s_key, Button(bx, by, 150, 38, "COMPRAR", font_s, color=(40, 80, 40))))

    char_btns = []
    char_back_btn = Button(0.5, 0.92, 300, 50, "VOLTAR", font_m, color=(80, 30, 30))
    for i, (char_id, char_data) in enumerate(CHAR_DATA.items()):
        x_ratio = 0.25 + i * 0.25
        locked = char_data["id"] not in save_data["unlocks"]
        lock_req = ACHIEVEMENTS.get(char_data["id"], {}).get("desc", "") if locked else ""
        btn = Button(x_ratio, 0.78, 280, 55, char_data["name"], font_m,
                     locked=locked, lock_req=lock_req)
        btn.x_ratio = x_ratio
        char_btns.append(btn)

    diff_btns = []
    diff_back_btn = Button(0.5, 0.92, 300, 50, "VOLTAR", font_m, color=(80, 30, 30))
    diff_order = ["FÁCIL", "MÉDIO", "DIFÍCIL", "HARDCORE"]
    for i, diff_name in enumerate(diff_order):
        diff_data = DIFFICULTIES[diff_name]
        locked = diff_data["id"] not in save_data["unlocks"]
        lock_req = ACHIEVEMENTS.get(diff_data["id"], {}).get("desc", "") if locked else ""
        diff_btns.append(Button(0.5, 0.30 + i * 0.13, 500, 60,
                                diff_name, font_m,
                                color=(30, 60, 30),
                                subtext=diff_data["desc"],
                                locked=locked, lock_req=lock_req))

    pact_btns = []
    pact_back_btn = Button(0.5, 0.92, 300, 50, "VOLTAR", font_m, color=(80, 30, 30))
    for i, (pact_name, pact_data) in enumerate(PACTOS.items()):
        pact_btns.append(Button(0.5, 0.30 + i * 0.14, 500, 60,
                                pact_data["name"], font_m,
                                color=(40, 20, 60),
                                subtext=pact_data["desc"]))

    bg_btns = []
    bg_back_btn = Button(0.5, 0.92, 300, 50, "VOLTAR", font_m, color=(80, 30, 30))
    bg_choices = list(BG_DATA.keys())
    for i, bg_key in enumerate(bg_choices):
        bg_btns.append(Button(0.5, 0.28 + i * 0.14, 400, 55,
                              bg_key.upper(), font_m))

    pause_btns = [
        Button(0.5, 0.55, 350, 60, "CONTINUAR", font_m, color=(30, 80, 30)),
        Button(0.5, 0.68, 350, 60, "MENU PRINCIPAL", font_m, color=(80, 30, 30)),
    ]
    pause_save_btns = [
        Button(0.70, 0.54, 260, 44, "SALVAR SLOT 1", font_s, color=(35, 80, 35)),
        Button(0.70, 0.61, 260, 44, "SALVAR SLOT 2", font_s, color=(35, 80, 35)),
        Button(0.70, 0.68, 260, 44, "SALVAR SLOT 3", font_s, color=(35, 80, 35)),
    ]
    game_over_btn = Button(0.5, 0.78, 420, 60, "VOLTAR AO MENU PRINCIPAL", font_m, color=(80, 30, 30))

    # Variáveis de estado do jogo
    state = "MENU"
    running = True
    m_pos = (0, 0)
    hitstop_timer = 0.0
    shake_timer = 0.0
    shake_strength = 0
    shake_offset = pygame.Vector2(0, 0)
    up_options = []
    run_gold_collected = 0.0
    autosave_timer = 0.0
    pause_save_feedback_timer = 0.0
    
    # Inicializa temp_settings para evitar UnboundLocalError
    temp_settings = json.loads(json.dumps(settings))

    # Loop principal refatorado
    last_res = (SCREEN_W, SCREEN_H)
    while running:
        # 1. Delta Time (dt) com Clamp
        dt_raw = clock.tick(FPS) / 1000.0
        dt = min(dt_raw, 1/30.0) # Evita bugs de física com lag

        if pause_save_feedback_timer > 0:
            pause_save_feedback_timer = max(0.0, pause_save_feedback_timer - dt_raw)
        
        # Atualiza posição do mouse
        m_pos = pygame.mouse.get_pos()

        # Se a resolução mudou, atualiza a posição de todos os botões
        if (SCREEN_W, SCREEN_H) != last_res:
            last_res = (SCREEN_W, SCREEN_H)
            for b in menu_btns: b.update_rect()
            for b in saves_slot_btns: b.update_rect()
            saves_back_btn.update_rect()
            for b in mission_btns: b.update_rect()
            for b in mission_claim_btns: b.update_rect()
            shop_back_btn.update_rect()
            for _, _, b in shop_talent_btns: b.update_rect()
            for b in char_btns: b.update_rect()
            char_back_btn.update_rect()
            for b in diff_btns: b.update_rect()
            diff_back_btn.update_rect()
            for b in pact_btns: b.update_rect()
            pact_back_btn.update_rect()
            for b in bg_btns: b.update_rect()
            bg_back_btn.update_rect()
            for b in pause_btns: b.update_rect()
            for b in pause_save_btns: b.update_rect()
            game_over_btn.update_rect()
            for b in settings_main_btns: b.update_rect()
            for b in settings_action_btns.values(): b.update_rect()

        # Lógica de Hit-Stop
        if hitstop_timer > 0:
            hitstop_timer -= dt_raw
            dt = 0 # Pausa a lógica do jogo, mas continua desenhando

        # 2. Manipulação de Eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                save_run_slot(0)
                save_game()
                running = False
            
            if event.type == pygame.KEYDOWN:
                if state == "SETTINGS" and settings_category == "controls" and settings_control_waiting:
                    if event.key == pygame.K_ESCAPE:
                        settings_control_waiting = None
                    else:
                        if "controls" not in temp_settings or not isinstance(temp_settings["controls"], dict):
                            temp_settings["controls"] = _deepcopy_settings(load_settings(force_default=True))["controls"]
                        if settings_control_waiting in temp_settings["controls"]:
                            temp_settings["controls"][settings_control_waiting] = pygame.key.name(event.key)
                            settings = _deepcopy_settings(temp_settings)
                            save_settings(settings)
                        settings_control_waiting = None
                        if snd_click: snd_click.play()
                    continue

                if state == "UPGRADE":
                    selected_idx = None
                    if event.key in [pygame.K_1, pygame.K_KP1]:
                        selected_idx = 0
                    elif event.key in [pygame.K_2, pygame.K_KP2]:
                        selected_idx = 1
                    elif event.key in [pygame.K_3, pygame.K_KP3]:
                        selected_idx = 2
                    elif event.key in [pygame.K_RETURN, pygame.K_KP_ENTER] and len(up_keys) > 0:
                        selected_idx = 0

                    if selected_idx is not None and selected_idx < len(up_keys):
                        if snd_click: snd_click.play()
                        apply_upgrade(up_keys[selected_idx])
                        up_options = []
                        up_keys = []
                        up_rarities = []
                        state = "PLAYING"
                        continue

                if event.key == pygame.K_ESCAPE:
                    if state == "PLAYING": state = "PAUSED"
                    elif state == "PAUSED": state = "PLAYING"
                    elif state == "SETTINGS":
                        if settings_category == "main":
                            state = "MENU"
                        else:
                            settings_category = "main"
                            temp_settings = json.loads(json.dumps(settings))
                    elif state in ["CHAR_SELECT", "MISSIONS", "SHOP", "BG_SELECT", "SAVES"]:
                        state = "MENU"
                    elif state == "DIFF_SELECT":
                        state = "CHAR_SELECT"
                    elif state == "PACT_SELECT":
                        state = "DIFF_SELECT"
                
                if event.key == get_control_key_code("pause"):
                    if state == "PLAYING": state = "PAUSED"
                    elif state == "PAUSED": state = "PLAYING"
                
                if event.key == get_control_key_code("dash"):
                    if state == "PLAYING" and player:
                        if player.start_dash(particles): play_sfx("dash")
                
                if event.key == get_control_key_code("ultimate"):
                    if state == "PLAYING" and player and player.ult_charge >= player.ult_max:
                        player.ult_charge = 0
                        damage_texts.add(DamageText(player.pos, "ULTIMATE!", True, (255, 0, 255)))
                        shake_timer = 1.0; shake_strength = 15
                        play_sfx("ult") 
                        
                        if player.char_id == 0: 
                            player.ult_active = True
                            player.ult_active_timer = 3.0 
                        elif player.char_id == 1: 
                            for i in range(36): 
                                angle = i * 10
                                v = pygame.Vector2(1, 0).rotate(angle)
                                shoot_angle = math.degrees(math.atan2(-v.y, v.x))
                                rotated_proj_frames = [pygame.transform.rotate(f, shoot_angle) for f in projectile_frames_raw]
                                p = Projectile(player.pos, v * PROJECTILE_SPEED, PROJECTILE_DMG * 3, rotated_proj_frames)
                                p.pierce = 5 
                                projectiles.add(p)
                        elif player.char_id == 2: 
                            for e in enemies:
                                e.frozen_timer = 5.0 
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                    click_pos = event.pos

                    if state == "SETTINGS":
                        start_settings_drag(click_pos)

                    if state == "MENU":
                        if menu_btns[0].rect.collidepoint(click_pos): 
                            state = "CHAR_SELECT"
                        elif menu_btns[1].rect.collidepoint(click_pos): 
                            state = "MISSIONS"
                        elif menu_btns[2].rect.collidepoint(click_pos): 
                            state = "SHOP"
                        elif menu_btns[3].rect.collidepoint(click_pos):
                            if snd_click: snd_click.play()
                            state = "SAVES"
                        elif menu_btns[4].rect.collidepoint(click_pos):
                            if snd_click: snd_click.play()
                            state = "BG_SELECT"
                        elif menu_btns[5].rect.collidepoint(click_pos): 
                            if snd_click: snd_click.play()
                            state = "SETTINGS"
                            settings_category = "main"
                            temp_settings = json.loads(json.dumps(settings))
                            # garante rect certo pro clique
                            for b in settings_main_btns: b.update_rect()
                            for b in settings_action_btns.values(): b.update_rect()
                        elif menu_btns[6].rect.collidepoint(click_pos): 
                            save_run_slot(0)
                            save_game()
                            running = False

                    elif state == "SAVES":
                        if saves_back_btn.rect.collidepoint(click_pos):
                            state = "MENU"
                        else:
                            for idx, btn in enumerate(saves_slot_btns):
                                if btn.rect.collidepoint(click_pos):
                                    if load_run_slot(idx):
                                        if snd_click: snd_click.play()
                                        autosave_timer = 0.0
                                        state = "PLAYING"
                                    break

                    elif state == "MISSIONS":
                        if mission_btns[0].rect.collidepoint(click_pos): 
                            state = "MENU"
                        for i, m in enumerate(save_data["daily_missions"]["active"]):
                            if m["completed"] and not m["claimed"]:
                                if mission_claim_btns[i].rect.collidepoint(click_pos):
                                    m["claimed"] = True
                                    save_data["gold"] += m["reward"]
                                    play_sfx("win")
                                    save_game()

                    elif state == "SHOP":
                        if shop_back_btn.rect.collidepoint(click_pos):
                            save_game()
                            state = "MENU"
                        else:
                            for p_name, s_key, btn in shop_talent_btns:
                                if btn.rect.collidepoint(click_pos):
                                    skill = TALENT_TREE[p_name]["skills"][s_key]
                                    lvl = save_data["perm_upgrades"].get(s_key, 0)
                                    if lvl < skill["max"]:
                                        price = skill["cost"][lvl]
                                        if save_data["gold"] >= price:
                                            save_data["gold"] -= price
                                            save_data["perm_upgrades"][s_key] = lvl + 1
                                            if snd_click: snd_click.play()

                    elif state == "CHAR_SELECT":
                        if char_back_btn.rect.collidepoint(click_pos): 
                            state = "MENU"
                        for i, btn in enumerate(char_btns):
                            if btn.rect.collidepoint(click_pos):
                                if snd_click: snd_click.play()
                                reset_game(i)
                                state = "DIFF_SELECT"

                    elif state == "DIFF_SELECT":
                        if diff_back_btn.rect.collidepoint(click_pos): 
                            state = "CHAR_SELECT"
                        diff_order = ["FÁCIL", "MÉDIO", "DIFÍCIL", "HARDCORE"]
                        for i, btn in enumerate(diff_btns):
                            if btn.rect.collidepoint(click_pos):
                                selected_difficulty = diff_order[i]
                                if snd_click: snd_click.play()
                                state = "PACT_SELECT"

                    elif state == "PACT_SELECT":
                        if pact_back_btn.rect.collidepoint(click_pos): 
                            state = "DIFF_SELECT"
                        pact_names = list(PACTOS.keys())
                        for i, btn in enumerate(pact_btns):
                            if btn.rect.collidepoint(click_pos):
                                selected_pact = pact_names[i]
                                if snd_click: snd_click.play()
                                p_data = PACTOS[selected_pact]
                                reset_game(player.char_id if player else 0)
                                run_gold_collected = 0.0
                                autosave_timer = 0.0
                                if p_data["hp"] > 0: player.hp = p_data["hp"]
                                state = "PLAYING"

                    elif state == "BG_SELECT":
                        if bg_back_btn.rect.collidepoint(click_pos):
                            state = "MENU"
                        else:
                            for i, btn in enumerate(bg_btns):
                                if btn.rect.collidepoint(click_pos):
                                    selected_bg = bg_choices[i]
                                    load_all_assets()
                                    if snd_click: snd_click.play()
                                    break

                    elif state == "SETTINGS":
                        # categorias (sempre clicáveis para facilitar navegação)
                        for btn in settings_main_btns:
                            if btn.rect.collidepoint(click_pos):
                                if snd_click: snd_click.play()
                                label = btn.text.strip().lower()
                                if "vídeo" in label or "video" in label:
                                    settings_category = "video"
                                elif "áudio" in label or "audio" in label:
                                    settings_category = "audio"
                                elif "controles" in label:
                                    settings_category = "controls"
                                elif "gameplay" in label:
                                    settings_category = "gameplay"
                                elif "acessibilidade" in label:
                                    settings_category = "accessibility"
                                if settings_category != "main":
                                    temp_settings = json.loads(json.dumps(settings))
                                break

                        # ações
                        for key, btn in settings_action_btns.items():
                            if btn.rect.collidepoint(click_pos):
                                if snd_click: snd_click.play()

                                if key == "apply":
                                    settings = json.loads(json.dumps(temp_settings))
                                    apply_settings(settings)
                                    load_all_assets()
                                    save_settings(settings)

                                elif key == "default":
                                    default_settings = load_settings(force_default=True)
                                    temp_settings = json.loads(json.dumps(default_settings))
                                    settings = json.loads(json.dumps(default_settings))
                                    apply_settings(settings)
                                    load_all_assets()
                                    save_settings(settings)

                                elif key == "back":
                                    if settings_category != "main":
                                        settings_category = "main"
                                    else:
                                        state = "MENU"
                                break

                        # opções internas da aba ativa
                        if settings_category == "video":
                            handle_video_settings_clicks(click_pos)
                        elif settings_category == "audio":
                            handle_audio_settings_clicks(click_pos)
                        elif settings_category == "controls":
                            handle_controls_settings_clicks(click_pos)
                        elif settings_category == "gameplay":
                            handle_gameplay_settings_clicks(click_pos)
                        elif settings_category == "accessibility":
                            handle_accessibility_settings_clicks(click_pos)

                    elif state == "GAME_OVER":
                        if game_over_btn.rect.collidepoint(click_pos):
                            if snd_click: snd_click.play()
                            clear_current_run_state()
                            run_gold_collected = 0.0
                            state = "MENU"

                    elif state == "UPGRADE":
                        for i in range(len(up_keys)):
                            y_pos = SCREEN_H*0.3 + i*150
                            rect = pygame.Rect(SCREEN_W/2 - 300, y_pos, 600, 120)
                            if rect.collidepoint(click_pos):
                                if snd_click: snd_click.play()
                                apply_upgrade(up_keys[i])
                                up_options = []
                                up_keys = []
                                up_rarities = []
                                state = "PLAYING"
                                break

                    elif state == "CHEST_UI":
                        auto_apply = settings["gameplay"].get("auto_apply_chest_reward", "On") == "On"
                        if not auto_apply:
                            box_w, box_h = 700, 100 + len(chest_loot) * 80
                            box_rect = pygame.Rect(SCREEN_W/2 - box_w/2, SCREEN_H/2 - box_h/2, box_w, box_h)
                            for i, loot in enumerate(chest_loot):
                                line_rect = pygame.Rect(box_rect.left + 20, box_rect.y + 25 + i * 80, box_w - 40, 70)
                                if line_rect.collidepoint(click_pos):
                                    apply_upgrade(loot)
                                    chest_loot = []
                                    chest_ui_timer = 0.0
                                    state = "PLAYING"
                                    if snd_click: snd_click.play()
                                    break

                    elif state == "PAUSED":
                        if pause_btns[0].rect.collidepoint(click_pos):
                            if snd_click: snd_click.play()
                            state = "PLAYING"
                        elif pause_btns[1].rect.collidepoint(click_pos):
                            if snd_click: snd_click.play()
                            save_run_slot(0)
                            clear_current_run_state()
                            run_gold_collected = 0.0
                            state = "MENU"
                        else:
                            for i, s_btn in enumerate(pause_save_btns):
                                if s_btn.rect.collidepoint(click_pos):
                                    if snd_click: snd_click.play()
                                    if save_run_slot(i):
                                        pause_save_feedback_timer = 2.0
                                    break

            if event.type == pygame.MOUSEMOTION and state == "SETTINGS":
                update_settings_drag(event.pos)

            if event.type == pygame.MOUSEBUTTONUP and state == "SETTINGS":
                stop_settings_drag()

                

        # 3. Atualização da Lógica do Jogo
        if state == "PLAYING" and player and player.hp > 0:

            current_xp_to_level = int(100 + (level-1)*25 + ((level-1)**1.15)*8)

            keys = pygame.key.get_pressed()
            
            shake_multiplier = max(0.0, min(1.0, settings["accessibility"].get("screen_shake", 100) / 100.0))
            if shake_timer > 0:
                shake_timer -= dt
                shake_offset.x = random.uniform(-shake_strength, shake_strength) * shake_multiplier
                shake_offset.y = random.uniform(-shake_strength, shake_strength) * shake_multiplier
            else:
                shake_offset.x = 0
                shake_offset.y = 0
            
            game_time += dt
            autosave_timer += dt
            if autosave_timer >= 15.0:
                save_run_slot(0)
                autosave_timer = 0.0
            update_mission_progress("time", dt)
            
            if REGEN_RATE > 0:
                player.hp = min(PLAYER_MAX_HP, player.hp + REGEN_RATE * dt)

            time_scale = 1.0 + (game_time / 60.0) * 0.20
            
            current_spawn_rate = max(0.1, SPAWN_EVERY_BASE - (game_time / 500.0)) 
            
            biome_type = BG_DATA[selected_bg]["type"]
            player.update(dt, keys, obstacles, particles_group=particles, biome_type=biome_type)
            
            if biome_type == "volcano" and player.iframes <= 0:
                if int(game_time * 2) % 5 == 0 and int((game_time - dt) * 2) % 5 != 0:
                    player.hp -= 0.05
                    damage_texts.add(DamageText(player.pos, "🔥", False, (255, 69, 0)))

            cam = pygame.Vector2(SCREEN_W/2, SCREEN_H/2) - player.pos + shake_offset

            if player.ult_active:
                if random.random() < 0.8:
                    particles.add(Particle(player.pos + pygame.Vector2(random.randint(-100,100), random.randint(-100,100)), (200, 200, 255), 6, 200, 0.4))
                
                for e in enemies:
                    if player.pos.distance_to(e.pos) < 250:
                        e.hp -= 2 
                        if random.random() < 0.2: damage_texts.add(DamageText(e.pos, 2, False, (255, 255, 0)))
                        if e.hp <= 0:
                            if player.ult_charge < player.ult_max: player.ult_charge += 1 
                            gems.add(Gem(e.pos, loader)); e.kill(); kills += 1

            shot_t += dt

            dynamic_cooldown = SHOT_COOLDOWN
            dmg_mult_fury = 1.0

            if HAS_FURY:
                hp_ratio = max(player.hp / PLAYER_MAX_HP, 0.0)
                fury = (1.0 - hp_ratio)  
                dmg_mult_fury = 1.0 + 0.60 * fury
                dynamic_cooldown = SHOT_COOLDOWN * (1.0 - 0.45 * fury)

            if shot_t >= dynamic_cooldown:
                shot_t = 0
                target = None
                best_d = SHOT_RANGE**2
                p_pos = player.pos
                for e in enemies:
                    if abs(e.pos.x - p_pos.x) > SHOT_RANGE or abs(e.pos.y - p_pos.y) > SHOT_RANGE:
                        continue
                    d2 = (e.pos - p_pos).length_squared()
                    if d2 < best_d: best_d = d2; target = e
                if target:
                    base_v = (target.pos - player.pos).normalize()
                    if player.char_id == 0: play_sfx("slash") 
                    else: play_sfx("shoot") 
                    
                    for i in range(PROJ_COUNT):
                        angle = -(15*(PROJ_COUNT-1))/2 + (i*15)
                        v = base_v.rotate(angle)
                        
                        if player.char_id == 0:
                            dmg_melee = int((PROJECTILE_DMG + 2) * dmg_mult_fury)
                            projectiles.add(MeleeSlash(player, v, dmg_melee, slash_frames_raw))
                        else:
                            shoot_angle = math.degrees(math.atan2(-v.y, v.x))
                            if has_bazuca:
                                rotated_proj_frames = [pygame.transform.scale(pygame.transform.rotate(f, shoot_angle), (300, 300)) for f in projectile_frames_raw]
                                p_dmg = PROJECTILE_DMG * 3
                            else:
                                rotated_proj_frames = [pygame.transform.rotate(f, shoot_angle) for f in projectile_frames_raw]
                                p_dmg = PROJECTILE_DMG

                            p_dmg = int(p_dmg * dmg_mult_fury)

                            projectiles.add(Projectile(player.pos, v * PROJECTILE_SPEED, p_dmg, rotated_proj_frames))

            if AURA_DMG > 0:
                aura_anim_timer += dt
                if aura_anim_timer > 0.1: aura_anim_timer = 0; aura_frame_idx = (aura_frame_idx + 1) % len(aura_frames)
                aura_t += dt
                if aura_t >= 0.4: 
                    aura_t = 0
                    current_aura_range = AURA_RANGE * 2 if has_buraco_negro else AURA_RANGE
                    current_aura_range *= BURN_AURA_MULT
                    current_aura_dmg = AURA_DMG * 3 if has_buraco_negro else AURA_DMG
                    current_aura_dmg *= FIRE_DMG_MULT
                    
                    for e in enemies:
                        if player.pos.distance_to(e.pos) < current_aura_range:
                            dmg_dealt = current_aura_dmg
                            
                            if HAS_INFERNO:
                                e.flash_timer = 0.5
                                dmg_dealt *= 1.25
                            is_crit = random.random() < CRIT_CHANCE
                            if is_crit:
                                dmg_dealt *= 2
                                hitstop_timer = 0.03
                            
                            e.hp -= dmg_dealt
                            e.flash_timer = 0.1 
                            damage_texts.add(DamageText(e.pos, dmg_dealt, is_crit, (200, 100, 255))) 
                            
                            if has_buraco_negro:
                                pull_dir = (player.pos - e.pos).normalize() if (player.pos - e.pos).length() > 0 else pygame.Vector2(0,0)
                                e.knockback += pull_dir * 18.0
                            
                            if e.hp <= 0: 
                                if player.ult_charge < player.ult_max: player.ult_charge += 1
                                gems.add(Gem(e.pos, loader)); e.kill(); kills += 1
            
            if ORB_COUNT > 0:
                rot_speed = 450 if has_serras else 150
                orb_rot_angle += rot_speed * dt
                current_orb_dmg = (ORB_DMG * 3) if has_serras else ORB_DMG
                
                for i in range(ORB_COUNT):
                    rad = math.radians(orb_rot_angle + i * (360/ORB_COUNT))
                    orb_p = player.pos + pygame.Vector2(math.cos(rad), math.sin(rad)) * ORB_DISTANCE
                    for e in enemies:
                        if orb_p.distance_to(e.pos) < 50:
                            tick_dmg = current_orb_dmg * dt * 10
                            if random.random() < CRIT_CHANCE: tick_dmg *= 2
                            
                            e.hp -= tick_dmg; 
                            if e.hp <= 0: 
                                if player.ult_charge < player.ult_max: player.ult_charge += 1
                                gems.add(Gem(e.pos, loader)); e.kill(); kills += 1

            spawn_t += dt
            
            current_int_time = int(game_time)
            if current_int_time % 60 == 0 and current_int_time > 0 and current_int_time not in triggered_hordes:
                triggered_hordes.add(current_int_time)
                damage_texts.add(DamageText(player.pos, "⚠️ HORDA! ⚠️", True, (255, 50, 50)))
                shake_timer = 1.0; shake_strength = 20
                play_sfx("ult") 
                enemy_count = 40 + int(game_time // 120) * 10
                radius = 900 
                for i in range(enemy_count):
                    angle = math.radians(i * (360 / enemy_count))
                    spawn_x = player.pos.x + math.cos(angle) * radius
                    spawn_y = player.pos.y + math.sin(angle) * radius
                    spawn_pos = pygame.Vector2(spawn_x, spawn_y)
                    kind = "tank" if current_int_time % 120 == 0 else "runner"
                    enemies.add(Enemy(kind, spawn_pos, loader, DIFFICULTIES[selected_difficulty], time_scale)) 

            if game_time >= BOSS_SPAWN_TIME * (bosses_spawned + 1):
                bosses_spawned += 1
                boss_pos = player.pos + pygame.Vector2(1200, 0) 
                enemies.add(Enemy("boss", boss_pos, loader, DIFFICULTIES[selected_difficulty], time_scale, boss_tier=bosses_spawned))
                
                warn_txt = font_l.render("⚠️ ALERTA DE CHEFÃO ⚠️", True, (255, 0, 0))
                screen.blit(warn_txt, warn_txt.get_rect(center=(SCREEN_W//2, SCREEN_H//2 - 200)))
                play_sfx("ult")

            if int(game_time) > 0 and int(game_time) % 120 == 0 and int(game_time) not in triggered_hordes:
                event_type = random.choice(["METEORO", "OURO", "SLIME", "DARKNESS"])
                triggered_hordes.add(int(game_time))
                if event_type == "METEORO":
                    damage_texts.add(DamageText(player.pos, "⚠️ CHUVA DE METEOROS! ⚠️", True, (255, 69, 0)))
                    for _ in range(15):
                        m_pos = player.pos + pygame.Vector2(random.randint(-800, 800), random.randint(-800, 800))
                        active_explosions.append(ExplosionAnimation(m_pos, 250, explosion_frames_raw))
                elif event_type == "OURO":
                    damage_texts.add(DamageText(player.pos, "💰 CHUVA DE OURO! 💰", True, (255, 215, 0)))
                    for _ in range(20):
                        drops.add(Drop(player.pos + pygame.Vector2(random.randint(-500, 500), random.randint(-500, 500)), "coin", loader))
                elif event_type == "SLIME":
                    damage_texts.add(DamageText(player.pos, "🟢 INVASÃO DE SLIMES! 🟢", True, (0, 255, 0)))
                    for _ in range(30):
                        enemies.add(Enemy("slime", player.pos + pygame.Vector2(random.randint(-900, 900), random.randint(-900, 900)), loader, DIFFICULTIES[selected_difficulty], time_scale))
                elif event_type == "DARKNESS":
                    damage_texts.add(DamageText(player.pos, "🌑 ESCURIDÃO TOTAL! 🌑", True, (100, 100, 255)))
                    darkness_timer = 30.0

            if int(game_time) == 240 and "ARENA_EVENT" not in triggered_hordes:
                triggered_hordes.add("ARENA_EVENT")
                damage_texts.add(DamageText(player.pos, "🏟️ ARENA DE PAREDES! 🏟️", True, (255, 255, 0)))
                for i in range(24):
                    angle = math.radians(i * (360/24))
                    wall_pos = player.pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * 600
                    obstacles.add(Obstacle(wall_pos, loader, random.randint(0, 3)))
                
            if spawn_t >= current_spawn_rate:
                spawn_t = 0
                sp = player.pos + pygame.Vector2(random.choice([-1,1])*1100, random.randint(-600,600))
                
                spawn_list = ["runner", "tank", "shooter"]
                spawn_weights = [50, 30, 20]
                
                if selected_difficulty in ["DIFÍCIL", "HARDCORE"]:
                    spawn_list.extend(["slime", "robot"])
                    spawn_weights.extend([15, 15]) 
                
                if game_time < 30:
                    enemies.add(Enemy("runner", sp, loader, DIFFICULTIES[selected_difficulty], time_scale))
                else:
                    chosen_enemy = random.choices(spawn_list, weights=spawn_weights, k=1)[0]
                    elite_chance = min(0.15, 0.03 + (game_time / 480.0) * 0.05)
                    is_elite = random.random() < elite_chance
                    
                    enemies.add(Enemy(chosen_enemy, sp, loader, DIFFICULTIES[selected_difficulty], time_scale, is_elite=is_elite))

            enemies.update(dt, player.pos, cam, obstacles, enemy_projectiles, puddles, loader, selected_pact)
            puddles.update(dt, cam)
            projectiles.update(dt, cam)
            enemy_projectiles.update(dt, cam)
            gems.update(dt, cam, player.pos) 
            drops.update(dt, cam) 
            obstacles.update(dt, cam)
            damage_texts.update(dt, cam)
            particles.update(dt, cam) 

            now_ms = pygame.time.get_ticks()
            active_explosions = [exp for exp in active_explosions if exp.update(now_ms)]

            for p in list(projectiles):
                is_melee = getattr(p, "is_melee", False)
                if not is_melee:
                    hit_obs = False
                    for obs in obstacles:
                        if obs.hitbox.collidepoint(p.pos): p.kill(); hit_obs = True; break
                    if hit_obs: continue
                
                hits = pygame.sprite.spritecollide(p, enemies, False, projectile_enemy_collision)
                for hit in hits:
                    if hit not in p.hit_enemies:
                        dmg_dealt = p.dmg
                        is_crit = random.random() < CRIT_CHANCE
                        if is_crit:
                            dmg_dealt *= CRIT_DMG_MULT
                            hitstop_timer = 0.03
                        
                        hit.hp -= dmg_dealt
                        p.hit_enemies.append(hit)
                        play_sfx("hit") 

                        if EXECUTE_THRESH > 0 and hit.kind != "boss":
                            if hit.hp > 0 and (hit.hp / hit.max_hp) <= EXECUTE_THRESH:
                                hit.hp = 0
                        
                        hit.flash_timer = 0.1 
                        
                        if is_melee:
                            knock_dir = (hit.pos - player.pos).normalize()
                            knock_force = 15.0 
                        else:
                            knock_dir = p.vel.normalize() if p.vel.length() > 0 else pygame.Vector2(1,0)
                            knock_force = 3.0 
                        
                        if HAS_CHAOS_BOLT and random.random() < 0.15:
                            active_explosions.append(ExplosionAnimation(hit.pos, 150, explosion_frames_raw))
                            hit.hp -= PROJECTILE_DMG * 2

                        if hit.kind == "boss": knock_force *= 0.1
                        hit.knockback += knock_dir * knock_force
                        
                        d_color = (255, 200, 0) if is_melee else (255, 255, 255)
                        damage_texts.add(DamageText(hit.pos, dmg_dealt, is_crit, d_color))
                        
                        has_explosion = EXPLOSION_RADIUS > 0 or has_bazuca
                        if has_explosion:
                            current_exp_rad = EXPLOSION_RADIUS + 150 if has_bazuca else EXPLOSION_RADIUS
                            current_exp_rad *= EXPLOSION_SIZE_MULT
                            current_exp_dmg = EXPLOSION_DMG * 3 if has_bazuca else EXPLOSION_DMG
                            
                            exp_pos = pygame.Vector2(p.pos)
                            active_explosions.append(ExplosionAnimation(exp_pos, current_exp_rad, explosion_frames_raw))
                            play_sfx("explosion") 
                            for e in enemies:
                                if exp_pos.distance_to(e.pos) < current_exp_rad: 
                                    exp_dmg_dealt = current_exp_dmg
                                    exp_is_crit = random.random() < CRIT_CHANCE
                                    if exp_is_crit:
                                        exp_dmg_dealt *= 2
                                        hitstop_timer = 0.03
                                    
                                    e.hp -= exp_dmg_dealt
                                    e.flash_timer = 0.1 
                                    exp_dir = (e.pos - exp_pos).normalize() if (e.pos - exp_pos).length() > 0 else pygame.Vector2(1,0)
                                    e.knockback += exp_dir * 8.0 
                                    damage_texts.add(DamageText(e.pos, exp_dmg_dealt, exp_is_crit, (255, 100, 0))) 
                        
                        if hit.hp <= 0: 
                            if player.ult_charge < player.ult_max: player.ult_charge += 1
                            gems.add(Gem(hit.pos, loader)); hit.kill(); kills += 1
                            save_data["stats"]["total_kills"] += 1
                            update_mission_progress("kills", 1)
                            if hit.kind == "boss":
                                session_boss_kills += 1
                                save_data["stats"]["boss_kills"] += 1
                                update_mission_progress("boss", 1)
                                drops.add(Drop(hit.pos, "chest", loader))
                            elif random.random() < DROP_CHANCE:
                                drops.add(Drop(hit.pos, "coin", loader))

                            # Salva imediatamente ao desbloquear metas de personagem (Caçador/Mago).
                            check_achievements(save_when_unlocked=True)
                        
                        # Lógica de Ricochete e Perfuração (Apenas para Projéteis)
                        if not is_melee:
                            if p.ricochet > 0:
                                p.ricochet -= 1
                                p.hit_enemies.pop()
                                
                                new_target = None
                                min_dist = float("inf")
                                for e in enemies:
                                    if e not in p.hit_enemies and e != hit:
                                        dist = p.pos.distance_to(e.pos)
                                        if dist < min_dist:
                                            min_dist = dist
                                            new_target = e
                                if new_target:
                                    p.vel = (new_target.pos - p.pos).normalize() * PROJECTILE_SPEED
                                else:
                                    p.kill()
                            elif len(p.hit_enemies) > p.pierce:
                                p.kill()

            for p in list(enemy_projectiles):
                if p.rect.colliderect(player.rect) and player.iframes <= 0:
                    player.hp -= p.dmg * (1.0 - DAMAGE_RES)
                    player.iframes = 0.5
                    play_sfx("hurt")
                    p.kill()
                    if THORNS_PERCENT > 0:
                        owner = getattr(p, "owner", None)
                        if owner and owner.hp > 0:
                            reflected_dmg = p.dmg * THORNS_PERCENT
                            owner.hp -= reflected_dmg
                            damage_texts.add(DamageText(owner.pos, int(reflected_dmg), False, (255, 0, 255)))

            for g in list(gems):
                if g.rect.colliderect(player.rect):
                    xp += 10; g.kill(); play_sfx("gem")

            for d in list(drops):
                if d.rect.colliderect(player.rect):
                    if d.kind == "coin":
                        coin_value = 50 * DIFFICULTIES[selected_difficulty]["gold_mult"]
                        run_gold_collected += coin_value
                        save_data["gold"] += coin_value
                        update_mission_progress("gold", coin_value)
                        play_sfx("drop")
                        d.kill()
                    elif d.kind == "chest":
                        auto_pickup = settings["gameplay"].get("auto_pickup_chest", "On") == "On"
                        if not auto_pickup and not is_control_pressed(keys, "dash"):
                            continue

                        chest_loot = pick_upgrades_with_synergy(list(UPGRADE_POOL.keys()), player_upgrades, k=3)
                        auto_apply = settings["gameplay"].get("auto_apply_chest_reward", "On") == "On"
                        if auto_apply:
                            for loot in chest_loot:
                                apply_upgrade(loot)
                            chest_loot = []
                        else:
                            state = "CHEST_UI"
                            chest_ui_timer = 5.0
                        d.kill()

            for p in list(puddles):
                if p.hitbox.colliderect(player.rect) and player.iframes <= 0:
                    player.hp -= 0.5 * dt

            if xp >= current_xp_to_level:
                level += 1
                session_max_level = max(session_max_level, level)
                update_mission_progress("level", level, is_absolute=True)
                xp = 0
                state = "UPGRADE"
                play_sfx("levelup")
                up_keys, up_rarities = [], []
                options = pick_upgrades_with_synergy(list(UPGRADE_POOL.keys()), player_upgrades)
                for opt in options:
                    rarity_roll = random.random()
                    chosen_rarity = "COMUM"
                    for r_name, r_data in RARITIES.items():
                        if rarity_roll < r_data["chance"]: chosen_rarity = r_name; break
                    up_keys.append(opt)
                    up_rarities.append((chosen_rarity, RARITIES[chosen_rarity]))

            if player.hp <= 0:
                play_sfx("lose")
                state = "GAME_OVER"
                save_run_slot(0)
                save_data["stats"]["deaths"] += 1
                save_data["stats"]["total_time"] += game_time
                save_data["stats"]["max_level_reached"] = max(save_data["stats"]["max_level_reached"], session_max_level)
                check_achievements()
                save_game()

        elif state == "CHEST_UI":
            auto_apply = settings["gameplay"].get("auto_apply_chest_reward", "On") == "On"
            if auto_apply:
                chest_ui_timer -= dt
                if chest_ui_timer <= 0:
                    for loot in chest_loot:
                        apply_upgrade(loot)
                    chest_loot = []
                    state = "PLAYING"

        # 4. Desenho na Tela
        screen.fill((0, 0, 0))

        # Lógica de desenho baseada no estado
        if state == "MENU":
            screen.blit(menu_bg_img, (0,0))
            # O título já faz parte da imagem de fundo (Underworld Hero)
            for b in menu_btns: b.check_hover(m_pos, snd_hover); b.draw(screen)

        elif state == "SAVES":
            screen.blit(menu_bg_img, (0,0))
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180)); screen.blit(overlay, (0, 0))
            t = font_l.render("SAVES / PROGRESSO", True, (255, 255, 255))
            screen.blit(t, t.get_rect(center=(SCREEN_W//2, SCREEN_H*0.14)))

            for idx, btn in enumerate(saves_slot_btns):
                slot_path = get_run_slot_path(idx)
                slot_exists = os.path.exists(slot_path)
                btn.text = f"SLOT {idx + 1} - {'DISPONÍVEL' if slot_exists else 'VAZIO'}"
                btn.color = (40, 90, 40) if slot_exists else (60, 60, 70)
                btn.check_hover(m_pos, snd_hover)
                btn.draw(screen)

            saves_back_btn.check_hover(m_pos, snd_hover)
            saves_back_btn.draw(screen)

        elif state == "MISSIONS":
            screen.blit(menu_bg_img, (0,0))
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180)); screen.blit(overlay, (0, 0))
            t = font_l.render("MISSÕES DIÁRIAS", True, (255, 215, 0))
            screen.blit(t, t.get_rect(center=(SCREEN_W//2, SCREEN_H*0.12)))

            now_dt = datetime.now()
            next_reset = (now_dt + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            remaining = max(0, int((next_reset - now_dt).total_seconds()))
            rem_h = remaining // 3600
            rem_m = (remaining % 3600) // 60
            rem_s = remaining % 60
            timer_txt = font_s.render(f"RESET EM: {rem_h:02}:{rem_m:02}:{rem_s:02}", True, (255, 240, 140))
            screen.blit(timer_txt, timer_txt.get_rect(center=(SCREEN_W//2, SCREEN_H*0.18)))
            
            for i, m in enumerate(save_data["daily_missions"]["active"]):
                y_base = SCREEN_H * 0.29 + i * 120
                box_rect = pygame.Rect(SCREEN_W/2 - 300, y_base, 600, 100)
                pygame.draw.rect(screen, (30, 30, 50, 200), box_rect, border_radius=10)
                pygame.draw.rect(screen, (100, 100, 255), box_rect, 2, border_radius=10)

                title = font_m.render(m['name'], True, (255, 255, 100))
                screen.blit(title, (box_rect.x + 20, box_rect.y + 10))
                desc = font_s.render(m['desc'], True, (200, 200, 200))
                screen.blit(desc, (box_rect.x + 20, box_rect.y + 55))

                progress = m['progress'] / m['goal']
                prog_bar_rect = pygame.Rect(box_rect.x + 20, box_rect.y + 80, 300, 15)
                pygame.draw.rect(screen, (0,0,0), prog_bar_rect)
                pygame.draw.rect(screen, (0, 255, 0), (prog_bar_rect.x, prog_bar_rect.y, prog_bar_rect.width * progress, prog_bar_rect.height))
                pygame.draw.rect(screen, (255,255,255), prog_bar_rect, 1)

                if m['completed']:
                    if m['claimed']:
                        claim_txt = font_s.render("COLETADO!", True, (100, 255, 100))
                        screen.blit(claim_txt, (box_rect.right - 150, box_rect.centery - 10))
                    else:
                        mission_claim_btns[i].check_hover(m_pos, snd_hover)
                        mission_claim_btns[i].draw(screen)
            
            mission_btns[0].check_hover(m_pos, snd_hover); mission_btns[0].draw(screen)

        elif state == "SHOP":
            screen.blit(menu_bg_img, (0,0))
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180)); screen.blit(overlay, (0, 0))
            t = font_l.render("ÁRVORE DE TALENTOS", True, (255, 215, 0))
            screen.blit(t, t.get_rect(center=(SCREEN_W//2, SCREEN_H*0.1)))
            gold_txt = font_m.render(f"OURO: {save_data['gold']}", True, (255, 215, 0))
            screen.blit(gold_txt, gold_txt.get_rect(topright=(SCREEN_W - 30, 20)))

            path_names = list(TALENT_TREE.keys())
            for p_idx, p_name in enumerate(path_names):
                path = TALENT_TREE[p_name]
                px = int(SCREEN_W * 0.1)
                py = int(SCREEN_H * (0.22 + p_idx * 0.22))
                
                p_title = font_m.render(path["title"], True, (255, 255, 255))
                screen.blit(p_title, (px, py))
                p_desc = font_s.render(path["desc"], True, (180, 180, 180))
                screen.blit(p_desc, (px, py + 40))

                skill_keys = list(path["skills"].keys())
                for s_idx, s_key in enumerate(skill_keys):
                    skill = path["skills"][s_key]
                    lvl = save_data["perm_upgrades"].get(s_key, 0)
                    sy = py + 80 + s_idx * 45
                    
                    s_txt = font_s.render(f"{skill['name']} ({lvl}/{skill['max']})", True, (255, 255, 100))
                    screen.blit(s_txt, (px + 50, sy))
                    sd_txt = pygame.font.SysFont("Arial", 18).render(skill["desc"], True, (200, 200, 200))
                    screen.blit(sd_txt, (px + 300, sy + 5))

                    btn_found = [b for name, key, b in shop_talent_btns if name == p_name and key == s_key][0]
                    if lvl < skill["max"]:
                        price = skill["cost"][lvl]
                        btn_found.text = f"{price} G"
                        btn_found.color = (40, 100, 40) if save_data["gold"] >= price else (100, 40, 40)
                    else:
                        btn_found.text = "MAX"
                        btn_found.color = (60, 60, 60)
                    
                    btn_found.update_rect()
                    btn_found.check_hover(m_pos, snd_hover)
                    btn_found.draw(screen)

            shop_back_btn.check_hover(m_pos, snd_hover); shop_back_btn.draw(screen)
        
        elif state == "CHAR_SELECT":
            screen.blit(menu_bg_img, (0,0))
            t = font_l.render("", True, (255,255,255))
            screen.blit(t, t.get_rect(center=(SCREEN_W//2, SCREEN_H*0.15)))
            
            time_ms = pygame.time.get_ticks()
            frame_idx = int((time_ms / 100) % 10)
            
            for i, anim in enumerate(menu_char_anims):
                btn = char_btns[i]
                img = anim[frame_idx]
                if btn.locked:
                    img = img.copy()
                    img.fill((0, 0, 0, 255), special_flags=pygame.BLEND_RGBA_MULT)
                
                x_pos = int(SCREEN_W * btn.x_ratio)
                float_offset = math.sin((time_ms + i * 500) / 300.0) * 15
                y_pos = int(SCREEN_H * 0.40) + float_offset
                rect = img.get_rect(center=(x_pos, y_pos))
                
                if btn.is_hovered and not btn.locked:
                    pygame.draw.circle(screen, (0, 100, 150), rect.center, 120)
                    pygame.draw.circle(screen, (0, 255, 255), rect.center, 120, 3)
                screen.blit(img, rect)
            for b in char_btns: b.check_hover(m_pos, snd_hover); b.draw(screen)
            char_back_btn.check_hover(m_pos, snd_hover); char_back_btn.draw(screen)
        
        elif state == "DIFF_SELECT":
            screen.blit(menu_bg_img, (0,0))
            t = font_l.render("SELECIONE A DIFICULDADE", True, (255,255,255))
            screen.blit(t, t.get_rect(center=(SCREEN_W//2, SCREEN_H*0.15)))
            
            for btn in diff_btns:
                btn.check_hover(m_pos, snd_hover)
                btn.draw(screen)
            diff_back_btn.check_hover(m_pos, snd_hover); diff_back_btn.draw(screen)

        elif state == "PACT_SELECT":
            screen.blit(menu_bg_img, (0,0))
            t = font_l.render("ESCOLHA SEU PACTO", True, (255, 100, 100))
            screen.blit(t, t.get_rect(center=(SCREEN_W//2, SCREEN_H*0.15)))
            for btn in pact_btns:
                btn.check_hover(m_pos, snd_hover)
                btn.draw(screen)
            pact_back_btn.check_hover(m_pos, snd_hover); pact_back_btn.draw(screen)

        elif state == "SETTINGS":
            draw_settings_menu(screen, settings, temp_settings, settings_category, m_pos, font_l, font_m, font_s, clock)
            
        elif state == "BG_SELECT":
            screen.blit(menu_bg_img, (0,0))
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180)); screen.blit(overlay, (0, 0))
            t = font_l.render("", True, (0, 255, 255))
            screen.blit(t, t.get_rect(center=(SCREEN_W//2, SCREEN_H*0.12)))
            for i, b in enumerate(bg_btns):
                b.check_hover(m_pos, snd_hover)
                b.draw(screen)
                bg_key = bg_choices[i]
                preview_name = BG_DATA[bg_key]["name"]
                preview_img = loader.load_image(preview_name, (80, 80))
                preview_rect = preview_img.get_rect(midright=(b.rect.left - 20, b.rect.centery))
                screen.blit(preview_img, preview_rect)
                if bg_key == selected_bg:
                    pygame.draw.rect(screen, (0, 255, 0), b.rect.inflate(10, 10), 3, border_radius=14)
            bg_back_btn.check_hover(m_pos, snd_hover); bg_back_btn.draw(screen)
            
        elif state in ["PLAYING", "UPGRADE", "CHEST_UI", "GAME_OVER", "PAUSED"] and player is not None:
            cam = pygame.Vector2(SCREEN_W/2, SCREEN_H/2) - player.pos + shake_offset
            
            if 'darkness_timer' not in locals(): darkness_timer = 0.0
            if state == "PLAYING" and darkness_timer > 0: darkness_timer -= dt
            
            bg_w, bg_h = ground_img.get_size()
            st_x, st_y = int(cam.x % bg_w) - bg_w, int(cam.y % bg_h) - bg_h
            for x in range(st_x, SCREEN_W + bg_w, bg_w):
                if x + bg_w < 0 or x > SCREEN_W: continue
                for y in range(st_y, SCREEN_H + bg_h, bg_h): 
                    if y + bg_h < 0 or y > SCREEN_H: continue
                    screen.blit(ground_img, (x, y))
            
            puddles.draw(screen)
            obstacles.draw(screen); gems.draw(screen); drops.draw(screen); projectiles.draw(screen); enemy_projectiles.draw(screen); enemies.draw(screen)
            
            for e in enemies:
                if e.hp < e.max_hp or e.kind in ["boss", "elite"]:
                    bar_w = 120 if e.kind == "boss" else 60 if e.kind == "elite" else 40
                    bar_h = 10 if e.kind == "boss" else 6
                    bar_x = e.rect.centerx - bar_w // 2
                    bar_y = e.rect.top - 15
                    pygame.draw.rect(screen, (200, 0, 0), (bar_x, bar_y, bar_w, bar_h))
                    ratio = max(0, e.hp / e.max_hp)
                    pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, int(bar_w * ratio), bar_h))
                    pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_w, bar_h), 1)

            show_offscreen_arrows = settings["gameplay"].get("show_offscreen_arrows", "On") == "On"
            if show_offscreen_arrows:
                for e in enemies:
                    if e.kind != "boss" or screen.get_rect().colliderect(e.rect):
                        continue
                    center = pygame.Vector2(SCREEN_W//2, SCREEN_H//2)
                    target = pygame.Vector2(e.rect.center)
                    direction = target - center
                    if direction.length() > 0: direction = direction.normalize()
                    margin = 40
                    arrow_pos = center + direction * (min(SCREEN_W, SCREEN_H)//2 - margin)
                    arrow_pos.x = max(margin, min(SCREEN_W - margin, arrow_pos.x))
                    arrow_pos.y = max(margin, min(SCREEN_H - margin, arrow_pos.y))
                    angle = math.atan2(direction.y, direction.x)
                    p1 = arrow_pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * 20
                    p2 = arrow_pos + pygame.Vector2(math.cos(angle + 2.5), math.sin(angle + 2.5)) * 15
                    p3 = arrow_pos + pygame.Vector2(math.cos(angle - 2.5), math.sin(angle - 2.5)) * 15
                    pygame.draw.polygon(screen, (255, 0, 0), [p1, p2, p3])
                        
            if show_offscreen_arrows:
                for d in drops:
                    if d.kind != "chest" or screen.get_rect().colliderect(d.rect):
                        continue
                    center = pygame.Vector2(SCREEN_W//2, SCREEN_H//2)
                    target = pygame.Vector2(d.rect.center)
                    direction = target - center
                    if direction.length() > 0: direction = direction.normalize()
                    margin = 40
                    arrow_pos = center + direction * (min(SCREEN_W, SCREEN_H)//2 - margin)
                    arrow_pos.x = max(margin, min(SCREEN_W - margin, arrow_pos.x))
                    arrow_pos.y = max(margin, min(SCREEN_H - margin, arrow_pos.y))
                    angle = math.atan2(direction.y, direction.x)
                    p1 = arrow_pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * 20
                    p2 = arrow_pos + pygame.Vector2(math.cos(angle + 2.5), math.sin(angle + 2.5)) * 15
                    p3 = arrow_pos + pygame.Vector2(math.cos(angle - 2.5), math.sin(angle - 2.5)) * 15
                    pygame.draw.polygon(screen, (255, 215, 0), [p1, p2, p3])

            particles.draw(screen)
            damage_texts.draw(screen) 

            if 'darkness_timer' in locals() and darkness_timer > 0:
                dark_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                dark_surf.fill((0, 0, 0, 230))
                pygame.draw.circle(dark_surf, (0, 0, 0, 0), (SCREEN_W//2, SCREEN_H//2), 250)
                screen.blit(dark_surf, (0, 0))
            
            if AURA_DMG > 0:
                current_aura_range = AURA_RANGE * 2 if has_buraco_negro else AURA_RANGE
                if not hasattr(main, "_last_aura_range") or main._last_aura_range != current_aura_range:
                    main._last_aura_range = current_aura_range
                    main._aura_cache = [pygame.transform.scale(f, (current_aura_range*2, current_aura_range*2)) for f in aura_frames]
                    if has_buraco_negro:
                        for f in main._aura_cache: f.fill((100, 0, 150), special_flags=pygame.BLEND_RGB_MULT)
                
                img = main._aura_cache[aura_frame_idx]
                screen.blit(img, img.get_rect(center=(SCREEN_W//2, SCREEN_H//2)), special_flags=pygame.BLEND_RGBA_ADD)
                
            if ORB_COUNT > 0:
                for i in range(ORB_COUNT):
                    rad = math.radians(orb_rot_angle + i * (360/ORB_COUNT))
                    orb_p = player.pos + pygame.Vector2(math.cos(rad), math.sin(rad)) * ORB_DISTANCE
                    img = orb_img if not has_serras else pygame.transform.scale(orb_img, (80, 80))
                    screen.blit(img, img.get_rect(center=orb_p + cam))

            if player.ult_active and player.char_id == 0:
                img = pygame.transform.rotate(tornado_img, (pygame.time.get_ticks() / 5) % 360)
                screen.blit(img, img.get_rect(center=(SCREEN_W//2, SCREEN_H//2)), special_flags=pygame.BLEND_RGBA_ADD)

            for exp in active_explosions:
                exp.draw(screen, cam)

            screen.blit(player.image, player.rect)

            # HUD Minimalista e Compacta
            ui_multiplier = max(0.6, min(1.0, settings["accessibility"].get("ui_size", 100) / 100.0))
            hud_scale = 0.6 * ui_multiplier
            high_contrast = settings["accessibility"].get("high_contrast", "Off") == "On"
            
            # Barra de Vida (Canto Superior Esquerdo) - Mais fina e compacta
            bar_w, bar_h = int(200 * hud_scale), int(18 * hud_scale)
            hp_bg = (0, 0, 0) if high_contrast else (10, 10, 10)
            hp_fg = (255, 40, 40) if high_contrast else (200, 30, 30)
            hp_tc = (255, 255, 0) if high_contrast else (255, 255, 255)
            pygame.draw.rect(screen, hp_bg, (10, 10, bar_w, bar_h), border_radius=3)
            pygame.draw.rect(screen, hp_fg, (10, 10, int(bar_w * (player.hp/PLAYER_MAX_HP)), bar_h), border_radius=3)
            hp_text = font_s.render(f"{int(player.hp)}", True, hp_tc)
            screen.blit(hp_text, (10 + bar_w + 5, 8))

            # Barra de XP (Topo da tela, ultra fina)
            xp_bar_h = 4
            xp_bg = (0, 0, 0) if high_contrast else (20, 20, 20)
            xp_fg = (0, 255, 255) if high_contrast else (0, 180, 255)
            level_col = (255, 255, 0) if high_contrast else (200, 200, 200)
            pygame.draw.rect(screen, xp_bg, (0, 0, SCREEN_W, xp_bar_h))
            pygame.draw.rect(screen, xp_fg, (0, 0, int(SCREEN_W * (xp/current_xp_to_level)), xp_bar_h))
            level_text = font_s.render(f"L{level}", True, level_col)
            screen.blit(level_text, (SCREEN_W - 40, 5))

            # Cronômetro e Kills (Centro Superior) - Compactados
            time_m, time_s = divmod(int(game_time), 60)
            time_col = (255, 255, 0) if high_contrast else (255, 255, 255)
            time_text = font_s.render(f"{time_m:02}:{time_s:02} | KILLS: {kills}", True, time_col)
            time_rect = time_text.get_rect(midtop=(SCREEN_W//2, 8))
            pygame.draw.rect(screen, (0,0,0,100), time_rect.inflate(15, 4), border_radius=5)
            screen.blit(time_text, time_rect)

            # Habilidades (Canto Inferior Direito) - Minimalistas
            icon_size = int(45 * hud_scale)
            margin = 15
            
            # Dash
            dash_pos = (SCREEN_W - margin - icon_size//2, SCREEN_H - margin - icon_size//2)
            pygame.draw.circle(screen, (15, 15, 15), dash_pos, icon_size//2)
            if player.dash_cooldown_timer > 0:
                ratio = 1 - (player.dash_cooldown_timer / DASH_COOLDOWN)
                pygame.draw.arc(screen, (0, 120, 255), (dash_pos[0]-icon_size//2, dash_pos[1]-icon_size//2, icon_size, icon_size), math.pi/2, math.pi/2 + (2*math.pi*ratio), 4)
            else:
                pygame.draw.circle(screen, (0, 120, 255), dash_pos, icon_size//2, 2)

            # Ultimate
            ult_pos = (dash_pos[0] - icon_size - 15, dash_pos[1])
            pygame.draw.circle(screen, (15, 15, 15), ult_pos, icon_size//2)
            ult_ratio = player.ult_charge / player.ult_max
            ult_color = (200, 0, 200) if ult_ratio >= 1 else (80, 0, 80)
            pygame.draw.arc(screen, ult_color, (ult_pos[0]-icon_size//2, ult_pos[1]-icon_size//2, icon_size, icon_size), math.pi/2, math.pi/2 + (2*math.pi*ult_ratio), 4)
            if ult_ratio >= 1:
                pygame.draw.circle(screen, (200, 0, 200), ult_pos, icon_size//2, 1)

            if state == "UPGRADE":
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); overlay.fill((0,0,0,180)); screen.blit(overlay, (0,0))
                msg = font_l.render("NOVO NÍVEL!", True, (255,255,0)); screen.blit(msg, (SCREEN_W//2 - msg.get_width()//2, SCREEN_H*0.1))
                up_options = []
                for i, key in enumerate(up_keys):
                    y_pos = SCREEN_H*0.3 + i*150
                    rect = pygame.Rect(SCREEN_W/2 - 300, y_pos, 600, 120)
                    up_options.append(rect)
                    rarity_name, rarity_data = up_rarities[i]
                    pygame.draw.rect(screen, rarity_data["color"], rect, 4, border_radius=10)
                    pygame.draw.rect(screen, (30,30,40,200), rect.inflate(-8, -8), border_radius=7)
                    
                    icon = upg_images.get(key, loader.load_image("icon_default", (64, 64)))
                    screen.blit(icon, (rect.x + 20, rect.centery - 32))

                    title = font_m.render(key, True, (255,255,255))
                    screen.blit(title, (rect.x + 100, rect.y + 15))
                    desc = font_s.render(UPGRADE_POOL[key], True, (200,200,200))
                    screen.blit(desc, (rect.x + 100, rect.y + 60))
                    
                    rarity_txt = font_s.render(rarity_name, True, rarity_data["color"]); 
                    screen.blit(rarity_txt, (rect.right - rarity_txt.get_width() - 15, rect.y + 10))

            if state == "CHEST_UI":
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); overlay.fill((0,0,0,200)); screen.blit(overlay, (0,0))
                box_w, box_h = 700, 100 + len(chest_loot) * 80
                box_rect = pygame.Rect(SCREEN_W/2 - box_w/2, SCREEN_H/2 - box_h/2, box_w, box_h)
                pygame.draw.rect(screen, (50, 40, 30), box_rect, border_radius=15)
                pygame.draw.rect(screen, (255, 215, 0), box_rect, 3, border_radius=15)
                title = font_l.render("BAÚ DE TESOUROS!", True, (255, 215, 0))
                screen.blit(title, title.get_rect(center=(SCREEN_W//2, box_rect.top - 60)))

                for i, loot in enumerate(chest_loot):
                    base_y = box_rect.y + 60 + i * 80
                    icon_size = 64
                    padding_left = 40
                    icon_x = box_rect.left + padding_left + icon_size // 2
                    text_x = box_rect.left + padding_left + icon_size + 25

                    if loot in upg_images:
                        icon = upg_images[loot]
                        icon_rect = icon.get_rect(center=(icon_x, base_y))
                        screen.blit(icon, icon_rect)

                    text_color = (255, 100, 255) if loot in EVOLUTIONS else (255, 255, 255)
                    desc = EVOLUTIONS[loot]["desc"] if loot in EVOLUTIONS else ""
                        
                    txt = font_s.render(f"+ {loot} {('- ' + desc) if desc else ''}", True, text_color)
                    screen.blit(txt, (text_x, base_y - txt.get_height() // 2))
                        
                auto_txt = font_s.render("RECOMPENSA(S) APLICADA(S) AUTOMATICAMENTE", True, (150, 150, 150))
                screen.blit(auto_txt, auto_txt.get_rect(center=(SCREEN_W//2, box_rect.bottom + 40)))

                timer_txt = font_s.render(f"Voltando em {max(0, chest_ui_timer):.1f}s...", True, (120, 120, 120))
                auto_apply = settings["gameplay"].get("auto_apply_chest_reward", "On") == "On"
                if auto_apply:
                    screen.blit(timer_txt, timer_txt.get_rect(center=(SCREEN_W//2, box_rect.bottom + 75)))
                else:
                    click_txt = font_s.render("CLIQUE EM UMA OPÇÃO PARA APLICAR", True, (255, 220, 120))
                    screen.blit(click_txt, click_txt.get_rect(center=(SCREEN_W//2, box_rect.bottom + 75)))

            if state == "PAUSED":
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180)) 
                screen.blit(overlay, (0, 0))
                    
                msg = font_l.render("JOGO PAUSADO", True, (255, 255, 255))
                screen.blit(msg, (SCREEN_W//2 - msg.get_width()//2, SCREEN_H * 0.15))
                    
                panel_w, panel_h = 450, 550
                panel_x = int(SCREEN_W * 0.15)
                panel_y = int(SCREEN_H * 0.3)
                panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
                    
                pygame.draw.rect(screen, (30, 30, 45, 240), panel_rect, border_radius=15)
                pygame.draw.rect(screen, (0, 255, 255), panel_rect, 3, border_radius=15)
                    
                stat_title = font_m.render("STATUS DO HERÓI", True, (255, 215, 0))
                screen.blit(stat_title, stat_title.get_rect(center=(panel_rect.centerx, panel_rect.y + 40)))
                    
                stats_lines = [
                        f"VIDA MÁXIMA: {int(PLAYER_MAX_HP)}",
                        f"VELOCIDADE: {int(PLAYER_SPEED)}",
                        f"DANO BASE: {PROJECTILE_DMG}",
                        f"CRÍTICO: {int(CRIT_CHANCE*100)}%",
                        f"PROJÉTEIS (QTD): {PROJ_COUNT}",
                        f"PERFURAÇÃO: {PROJ_PIERCE}",
                        f"TEMPO DE RECARGA: {SHOT_COOLDOWN:.2f}s",
                        f"RAIO DE EXPLOSÃO: {EXPLOSION_RADIUS}",
                        f"DANO DE AURA: {AURA_DMG}",
                        f"QTD DE ORBES: {ORB_COUNT}",
                        f"ALCANCE (ÍMÃ): {int(PICKUP_RANGE)}"
                    ]
                    
                start_y = panel_rect.y + 100
                for idx, line in enumerate(stats_lines):
                        line_txt = font_s.render(line, True, (200, 220, 255))
                        screen.blit(line_txt, (panel_rect.x + 30, start_y + (idx * 40)))

                for b in pause_btns: 
                        b.check_hover(m_pos, snd_hover)
                        b.draw(screen)
                for b in pause_save_btns:
                    b.check_hover(m_pos, snd_hover)
                    b.draw(screen)
                if pause_save_feedback_timer > 0:
                    saved_txt = font_s.render("SLOT SALVO COM SUCESSO", True, (120, 255, 120))
                    saved_rect = saved_txt.get_rect(center=(int(SCREEN_W * 0.70), int(SCREEN_H * 0.76)))
                    screen.blit(saved_txt, saved_rect)

            if state == "GAME_OVER":
                overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA); overlay.fill((150,0,0,150)); screen.blit(overlay, (0,0))
                msg = font_l.render("GAME OVER", True, (255,255,255)); screen.blit(msg, (SCREEN_W//2 - msg.get_width()//2, SCREEN_H//2 - 50))
                minutes = int(game_time // 60)
                seconds = int(game_time % 60)
                time_msg = font_m.render(f"TEMPO SOBREVIVIDO: {minutes:02}:{seconds:02}", True, (255, 215, 0))
                screen.blit(time_msg, (SCREEN_W//2 - time_msg.get_width()//2, SCREEN_H//2 + 50))
                gold_run_msg = font_m.render(f"GOLD COLETADO: {int(run_gold_collected)}", True, (255, 255, 120))
                screen.blit(gold_run_msg, (SCREEN_W//2 - gold_run_msg.get_width()//2, SCREEN_H//2 + 105))
                game_over_btn.check_hover(m_pos, snd_hover)
                game_over_btn.draw(screen)
                
                if new_unlocks_this_session:
                    ul_title = font_s.render("NOVAS CONQUISTAS:", True, (0, 255, 0))
                    screen.blit(ul_title, (SCREEN_W//2 - ul_title.get_width()//2, SCREEN_H//2 + 120))
                    for i, name in enumerate(new_unlocks_this_session):
                        t = font_s.render(name, True, (200, 255, 200))
                        screen.blit(t, (SCREEN_W//2 - t.get_width()//2, SCREEN_H//2 + 150 + i*30))

        # versão
        w, h = screen.get_size()
        version_str = f"v{GAME_VERSION} ({BUILD_TYPE})"
        shadow = font_s.render(version_str, True, (0,0,0))
        text   = font_s.render(version_str, True, (160,160,160))
        rect = text.get_rect(bottomright=(w-12, h-10))
        screen.blit(shadow, (rect.x+1, rect.y+1))
        screen.blit(text, rect)
                        
        pygame.display.flip()

    pygame.quit()

# --- Variáveis do Menu de Configurações ---
settings_category = "main"  # 'main', 'video', 'audio', 'controls', 'gameplay', 'accessibility'
temp_settings = {}
settings_control_waiting = None
settings_dragging_slider = None

# --- Fontes temporárias para criação dos botões de configurações (fora do main) ---
# Esses botões são criados no escopo global; as fontes serão recriadas dentro do main().
_tmp_font_m = None  # Será inicializado após pygame.init() no main()
_tmp_font_s = None

# --- Funções do Menu de Configurações ---
def draw_settings_menu(screen, settings, temp_settings, category, m_pos, font_l, font_m, font_s, clock):
    screen.blit(menu_bg_img, (0,0))
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # Título e Informações
    title_text = font_l.render("CONFIGURAÇÕES", True, (255, 255, 255))
    screen.blit(title_text, title_text.get_rect(center=(SCREEN_W / 2, SCREEN_H * 0.1)))
    
    version_text = font_s.render(f"v1.0.0", True, (200, 200, 200))
    screen.blit(version_text, (20, 20))
    
    fps_text = font_s.render(f"FPS: {int(clock.get_fps())}", True, (200, 200, 200))
    screen.blit(fps_text, fps_text.get_rect(topright=(SCREEN_W - 20, 20)))

    if category == "main":
        draw_main_settings(screen, m_pos, font_m)
    elif category == "video":
        draw_video_settings(screen, temp_settings, m_pos, font_m, font_s)
    elif category == "audio":
        draw_audio_settings(screen, temp_settings, m_pos, font_m, font_s)
    elif category == "controls":
        draw_controls_settings(screen, temp_settings, m_pos, font_m, font_s)
    elif category == "gameplay":
        draw_gameplay_settings(screen, temp_settings, m_pos, font_m, font_s)
    elif category == "accessibility":
        draw_accessibility_settings(screen, temp_settings, m_pos, font_m, font_s)
    # elif category == "audio":
    #     draw_audio_settings(screen, temp_settings, m_pos, font_m, font_s)
    # ... etc.

    # Botões de Ação
    for btn in settings_action_btns.values():
        btn.check_hover(m_pos, snd_hover)
        btn.draw(screen)

def draw_main_settings(screen, m_pos, font_m):
    for btn in settings_main_btns:
        btn.check_hover(m_pos, snd_hover)
        btn.draw(screen)

def draw_video_settings(screen, temp_settings, m_pos, font_m, font_s):
    options = [
        ("Resolução", temp_settings["video"]["resolution"], ["1280x720", "1920x1080"]),
        ("Tela cheia", temp_settings["video"]["fullscreen"], ["Off", "On"]),
        ("VSync", temp_settings["video"]["vsync"], ["Off", "On"]),
        ("Limite de FPS", str(temp_settings["video"]["fps_limit"]), ["30", "60", "120"]),
        ("Mostrar FPS", temp_settings["video"]["show_fps"], ["Off", "On"])
    ]

    for i, (label, value, _) in enumerate(options):
        y_pos = SCREEN_H * 0.25 + i * 70
        draw_setting_option(screen, y_pos, label, value, font_m, font_s, m_pos)

def draw_setting_option(screen, y_pos, label, value, font_m, font_s, m_pos):
    row_rect = pygame.Rect(int(SCREEN_W * 0.16), int(y_pos), int(SCREEN_W * 0.68), 54)
    pygame.draw.rect(screen, (22, 22, 30, 210), row_rect, border_radius=10)
    pygame.draw.rect(screen, (80, 90, 120), row_rect, 2, border_radius=10)

    label_text = font_m.render(label, True, (240, 240, 240))
    label_rect = label_text.get_rect(midleft=(row_rect.x + 20, row_rect.centery))
    screen.blit(label_text, label_rect)

    value_rect = pygame.Rect(row_rect.right - 280, row_rect.y + 4, 260, row_rect.height - 8)
    is_hovered = value_rect.collidepoint(m_pos)
    
    color = (80, 80, 120) if is_hovered else (50, 50, 70)
    pygame.draw.rect(screen, color, value_rect, border_radius=8)
    pygame.draw.rect(screen, (150, 150, 255), value_rect, 2, border_radius=8)

    value_text = font_s.render(f"< {value} >", True, (255, 255, 0))
    screen.blit(value_text, value_text.get_rect(center=value_rect.center))
    
    return value_rect

def draw_audio_settings(screen, temp_settings, m_pos, font_m, font_s):
    options = [
        ("Música", temp_settings["audio"]["music"], range(0, 101, 10)),
        ("SFX", temp_settings["audio"]["sfx"], range(0, 101, 10)),
        ("Mudo", temp_settings["audio"]["mute"], ["Off", "On"])
    ]

    for i, (label, value, _) in enumerate(options):
        y_pos = SCREEN_H * 0.25 + i * 70
        # Para os sliders de volume, o valor é um número, então tratamos de forma diferente
        if label in ["Música", "SFX"]:
            draw_slider_option(screen, y_pos, label, value, font_m, font_s, m_pos)
        else:
            draw_setting_option(screen, y_pos, label, value, font_m, font_s, m_pos)

def draw_slider_option(screen, y_pos, label, value, font_m, font_s, m_pos):
    row_rect = pygame.Rect(int(SCREEN_W * 0.16), int(y_pos), int(SCREEN_W * 0.68), 54)
    pygame.draw.rect(screen, (22, 22, 30, 210), row_rect, border_radius=10)
    pygame.draw.rect(screen, (80, 90, 120), row_rect, 2, border_radius=10)

    label_text = font_m.render(label, True, (240, 240, 240))
    label_rect = label_text.get_rect(midleft=(row_rect.x + 20, row_rect.centery))
    screen.blit(label_text, label_rect)

    slider_rect = pygame.Rect(row_rect.right - 340, row_rect.y + 17, 240, 20)
    pygame.draw.rect(screen, (35, 35, 50), slider_rect, border_radius=5)
    
    handle_pos = slider_rect.x + int((value / 100) * slider_rect.width)
    pygame.draw.rect(screen, (0, 220, 120), (slider_rect.x, slider_rect.y, max(0, handle_pos - slider_rect.x), slider_rect.height), border_radius=5)
    pygame.draw.circle(screen, (255, 255, 255), (handle_pos, slider_rect.centery), 15)

    value_text = font_s.render(f"{value}%", True, (255, 255, 0))
    value_rect = value_text.get_rect(midleft=(slider_rect.right + 14, slider_rect.centery))
    screen.blit(value_text, value_rect)

    return slider_rect



# --- Lógica de Desenho e Interação do Menu de Configurações ---

# (Esta seção será preenchida com a lógica de desenho e interação)

# interação para cada submenu de configurações)

# configurações)


# --- Criação dos Botões do Menu de Configurações ---
# Os botões são inicializados em init_settings_buttons(), chamado dentro do main()
settings_main_btns = []
settings_action_btns = {}

def init_settings_buttons(font_m):
    """Inicializa os botões do menu de configurações. Deve ser chamado após pygame.init()."""
    global settings_main_btns, settings_action_btns
    settings_main_btns = [
        Button(0.5, 0.3, 400, 50, "Vídeo",         font_m),
        Button(0.5, 0.4, 400, 50, "Áudio",         font_m),
        Button(0.5, 0.5, 400, 50, "Controles",     font_m),
        Button(0.5, 0.6, 400, 50, "Gameplay",      font_m),
        Button(0.5, 0.7, 400, 50, "Acessibilidade",font_m),
    ]
    settings_action_btns = {
        "apply":   Button(0.25, 0.9, 200, 50, "Aplicar",          font_m, color=(40, 100, 40)),
        "default": Button(0.5,  0.9, 350, 50, "Restaurar Padrão", font_m, color=(100, 100, 40)),
        "back":    Button(0.75, 0.9, 200, 50, "Voltar",           font_m, color=(100, 40, 40)),
    }


def handle_settings_clicks(m_pos):
    global state, settings_category, temp_settings, settings

    if settings_category == "main":
        if settings_main_btns[0].check_hover(m_pos): settings_category = "video"; temp_settings = json.loads(json.dumps(settings))
        elif settings_main_btns[1].check_hover(m_pos): settings_category = "audio"; temp_settings = json.loads(json.dumps(settings))
        elif settings_main_btns[2].check_hover(m_pos): settings_category = "controls"; temp_settings = json.loads(json.dumps(settings))
        elif settings_main_btns[3].check_hover(m_pos): settings_category = "gameplay"; temp_settings = json.loads(json.dumps(settings))
        elif settings_main_btns[4].check_hover(m_pos): settings_category = "accessibility"; temp_settings = json.loads(json.dumps(settings))
        
        # O botão de voltar no menu principal de configurações retorna ao menu do jogo
        if settings_action_btns["back"].check_hover(m_pos):
            state = "MENU"

    else: # Estamos em um submenu
        # 1. Verificar botões de ação primeiro (Back, Apply, Default)
        # Usamos o evento MOUSEBUTTONDOWN processado no loop principal para evitar cliques múltiplos
        # Mas como handle_settings_clicks é chamado dentro de MOUSEBUTTONDOWN, podemos usar m_pos
        
        if settings_action_btns["back"].rect.collidepoint(m_pos):
            settings_category = "main"
            temp_settings = {}
            if snd_click: snd_click.play()
            return

        if settings_action_btns["apply"].rect.collidepoint(m_pos):
            settings = json.loads(json.dumps(temp_settings))
            save_settings(settings)
            apply_settings(settings)
            load_all_assets()
            settings_category = "main"
            if snd_click: snd_click.play()
            return

        if settings_action_btns["default"].rect.collidepoint(m_pos):
            default_settings = load_settings() 
            temp_settings[settings_category] = default_settings[settings_category]
            if snd_click: snd_click.play()
            return

        # 2. Se não clicou em ações, processar cliques específicos do submenu
        if settings_category == "video":
            handle_video_settings_clicks(m_pos)
        elif settings_category == "audio":
            handle_audio_settings_clicks(m_pos)
        elif settings_category == "controls":
            handle_controls_settings_clicks(m_pos)
        elif settings_category == "gameplay":
            handle_gameplay_settings_clicks(m_pos)
        elif settings_category == "accessibility":
            handle_accessibility_settings_clicks(m_pos)

def draw_controls_settings(screen, temp_settings, m_pos, font_m, font_s):
    if "controls" not in temp_settings or not isinstance(temp_settings["controls"], dict):
        temp_settings["controls"] = _deepcopy_settings(load_settings(force_default=True))["controls"]

    control_labels = {
        "up": "Cima",
        "down": "Baixo",
        "left": "Esquerda",
        "right": "Direita",
        "dash": "Dash",
        "ultimate": "Ultimate",
        "pause": "Pause"
    }

    options = [
        ("up", temp_settings["controls"]["up"]),
        ("down", temp_settings["controls"]["down"]),
        ("left", temp_settings["controls"]["left"]),
        ("right", temp_settings["controls"]["right"]),
        ("dash", temp_settings["controls"]["dash"]),
        ("ultimate", temp_settings["controls"]["ultimate"]),
        ("pause", temp_settings["controls"]["pause"])
    ]

    for i, (key_name, value) in enumerate(options):
        y_pos = SCREEN_H * 0.2 + i * 60
        display_value = value.upper()
        if settings_control_waiting == key_name:
            display_value = "PRESSIONE UMA TECLA..."
        draw_setting_option(screen, y_pos, control_labels[key_name], display_value, font_m, font_s, m_pos)

    reset_btn = Button(0.5, 0.8, 300, 50, "Resetar para Padrão", font_m, color=(120, 60, 60))
    reset_btn.check_hover(m_pos, snd_hover)
    reset_btn.draw(screen)

def handle_audio_settings_clicks(m_pos):
    global temp_settings, settings
    options = {
        "Música": {"key": "music", "values": list(range(0, 101, 10))},
        "SFX": {"key": "sfx", "values": list(range(0, 101, 10))},
        "Mudo": {"key": "mute", "values": ["Off", "On"]}
    }

    y_pos_start = SCREEN_H * 0.25
    for i, (label, data) in enumerate(options.items()):
        y_pos = y_pos_start + i * 70
        key = data["key"]
        values = data["values"]

        if label in ["Música", "SFX"]:
            row_rect = pygame.Rect(int(SCREEN_W * 0.16), int(y_pos), int(SCREEN_W * 0.68), 54)
            slider_rect = pygame.Rect(row_rect.right - 340, row_rect.y + 17, 240, 20)
            if slider_rect.collidepoint(m_pos) and pygame.mouse.get_pressed()[0]:
                new_value = int(((m_pos[0] - slider_rect.x) / slider_rect.width) * 100)
                temp_settings["audio"][key] = max(0, min(100, new_value))
                settings = _deepcopy_settings(temp_settings)
                save_settings(settings)
                apply_audio_runtime(settings)
        else:
            row_rect = pygame.Rect(int(SCREEN_W * 0.16), int(y_pos), int(SCREEN_W * 0.68), 54)
            option_rect = pygame.Rect(row_rect.right - 280, row_rect.y + 4, 260, row_rect.height - 8)
            if option_rect.collidepoint(m_pos):
                current_value = temp_settings["audio"][key]
                current_index = values.index(str(current_value))
                new_index = (current_index + 1) % len(values)
                temp_settings["audio"][key] = values[new_index]
                settings = _deepcopy_settings(temp_settings)
                save_settings(settings)
                apply_audio_runtime(settings)

def draw_gameplay_settings(screen, temp_settings, m_pos, font_m, font_s):
    options = [
        ("Auto Coleta de Baú", temp_settings["gameplay"]["auto_pickup_chest"]),
        ("Auto Aplicar Recompensa", temp_settings["gameplay"]["auto_apply_chest_reward"]),
        ("Setas Fora da Tela", temp_settings["gameplay"]["show_offscreen_arrows"])
    ]

    for i, (label, value) in enumerate(options):
        y_pos = SCREEN_H * 0.25 + i * 70
        draw_setting_option(screen, y_pos, label, value, font_m, font_s, m_pos)

def handle_controls_settings_clicks(m_pos):
    global temp_settings, settings_control_waiting, settings
    if "controls" not in temp_settings or not isinstance(temp_settings["controls"], dict):
        temp_settings["controls"] = _deepcopy_settings(load_settings(force_default=True))["controls"]

    control_rows = [
        ("up", SCREEN_H * 0.2 + 0 * 60),
        ("down", SCREEN_H * 0.2 + 1 * 60),
        ("left", SCREEN_H * 0.2 + 2 * 60),
        ("right", SCREEN_H * 0.2 + 3 * 60),
        ("dash", SCREEN_H * 0.2 + 4 * 60),
        ("ultimate", SCREEN_H * 0.2 + 5 * 60),
        ("pause", SCREEN_H * 0.2 + 6 * 60),
    ]

    for action_name, y_pos in control_rows:
        value_rect = pygame.Rect(int(SCREEN_W * 0.16) + int(SCREEN_W * 0.68) - 280, int(y_pos) + 4, 260, 46)
        if value_rect.collidepoint(m_pos):
            settings_control_waiting = action_name
            return

    reset_btn_rect = pygame.Rect(SCREEN_W * 0.5 - 150, SCREEN_H * 0.8 - 25, 300, 50)
    if reset_btn_rect.collidepoint(m_pos):
        default_controls = {
            "up": "w", "down": "s", "left": "a", "right": "d",
            "dash": "space", "ultimate": "e", "pause": "p"
        }
        temp_settings["controls"] = default_controls
        settings = _deepcopy_settings(temp_settings)
        save_settings(settings)
        settings_control_waiting = None

def draw_accessibility_settings(screen, temp_settings, m_pos, font_m, font_s):
    options = [
        ("Screen Shake", temp_settings["accessibility"]["screen_shake"]),
        ("Tamanho da UI", temp_settings["accessibility"]["ui_size"]),
        ("Alto Contraste", temp_settings["accessibility"]["high_contrast"])
    ]

    for i, (label, value) in enumerate(options):
        y_pos = SCREEN_H * 0.25 + i * 70
        if label in ["Screen Shake", "Tamanho da UI"]:
            draw_slider_option(screen, y_pos, label, value, font_m, font_s, m_pos)
        else:
            draw_setting_option(screen, y_pos, label, value, font_m, font_s, m_pos)

def handle_gameplay_settings_clicks(m_pos):
    global temp_settings, settings
    options = {
        "Auto Coleta de Baú": {"key": "auto_pickup_chest", "values": ["Off", "On"]},
        "Auto Aplicar Recompensa": {"key": "auto_apply_chest_reward", "values": ["Off", "On"]},
        "Setas Fora da Tela": {"key": "show_offscreen_arrows", "values": ["Off", "On"]},
        "Dificuldade Padrão": {"key": "default_difficulty", "values": ["Fácil", "Médio", "Difícil", "Hardcore"]}
    }

    y_pos_start = SCREEN_H * 0.25
    for i, (label, data) in enumerate(options.items()):
        y_pos = y_pos_start + i * 70
        row_rect = pygame.Rect(int(SCREEN_W * 0.16), int(y_pos), int(SCREEN_W * 0.68), 54)
        option_rect = pygame.Rect(row_rect.right - 280, row_rect.y + 4, 260, row_rect.height - 8)
        if option_rect.collidepoint(m_pos):
            key = data["key"]
            values = data["values"]
            current_value = temp_settings["gameplay"][key]
            current_index = values.index(str(current_value))
            new_index = (current_index + 1) % len(values)
            temp_settings["gameplay"][key] = values[new_index]
            settings = _deepcopy_settings(temp_settings)
            save_settings(settings)

def handle_accessibility_settings_clicks(m_pos):
    global temp_settings, settings
    options = {
        "Screen Shake": {"key": "screen_shake", "values": list(range(0, 101, 10))},
        "Tamanho da UI": {"key": "ui_size", "values": [60, 80, 100]},
        "Alto Contraste": {"key": "high_contrast", "values": ["Off", "On"]}
    }

    y_pos_start = SCREEN_H * 0.25
    for i, (label, data) in enumerate(options.items()):
        y_pos = y_pos_start + i * 70
        key = data["key"]
        values = data["values"]

        if label in ["Screen Shake", "Tamanho da UI"]:
            row_rect = pygame.Rect(int(SCREEN_W * 0.16), int(y_pos), int(SCREEN_W * 0.68), 54)
            slider_rect = pygame.Rect(row_rect.right - 340, row_rect.y + 17, 240, 20)
            if slider_rect.collidepoint(m_pos) and pygame.mouse.get_pressed()[0]:
                if label == "Screen Shake":
                    new_value = int(((m_pos[0] - slider_rect.x) / slider_rect.width) * 100)
                    temp_settings["accessibility"][key] = max(0, min(100, new_value))
                else: # Tamanho da UI
                    new_value = int(60 + ((m_pos[0] - slider_rect.x) / slider_rect.width) * 40)
                    temp_settings["accessibility"][key] = max(60, min(100, new_value))
                settings = _deepcopy_settings(temp_settings)
                save_settings(settings)
        else:
            row_rect = pygame.Rect(int(SCREEN_W * 0.16), int(y_pos), int(SCREEN_W * 0.68), 54)
            option_rect = pygame.Rect(row_rect.right - 280, row_rect.y + 4, 260, row_rect.height - 8)
            if option_rect.collidepoint(m_pos):
                current_value = temp_settings["accessibility"][key]
                current_index = values.index(str(current_value))
                new_index = (current_index + 1) % len(values)
                temp_settings["accessibility"][key] = values[new_index]
                settings = _deepcopy_settings(temp_settings)
                save_settings(settings)

def handle_video_settings_clicks(m_pos):
    global temp_settings, settings
    options = {
        "Resolução": {"key": "resolution", "values": ["1280x720", "1920x1080"]},
        "Tela cheia": {"key": "fullscreen", "values": ["Off", "On"]},
        "VSync": {"key": "vsync", "values": ["Off", "On"]},
        "Limite de FPS": {"key": "fps_limit", "values": ["30", "60", "120"]},
        "Mostrar FPS": {"key": "show_fps", "values": ["Off", "On"]}
    }
    
    y_pos_start = SCREEN_H * 0.25
    for i, (label, data) in enumerate(options.items()):
        y_pos = y_pos_start + i * 70
        row_rect = pygame.Rect(int(SCREEN_W * 0.16), int(y_pos), int(SCREEN_W * 0.68), 54)
        option_rect = pygame.Rect(row_rect.right - 280, row_rect.y + 4, 260, row_rect.height - 8)
        if option_rect.collidepoint(m_pos):
            key = data["key"]
            values = data["values"]
            current_value = temp_settings["video"][key]
            current_index = values.index(str(current_value))
            new_index = (current_index + 1) % len(values)
            new_value = values[new_index]
            
            if key == "fps_limit":
                new_value = int(new_value)

            temp_settings["video"][key] = new_value
            settings = _deepcopy_settings(temp_settings)
            save_settings(settings)


def _slider_rect_for_category(category, key, y_pos):
    row_rect = pygame.Rect(int(SCREEN_W * 0.16), int(y_pos), int(SCREEN_W * 0.68), 54)
    if category == "audio" and key in ["music", "sfx"]:
        return pygame.Rect(row_rect.right - 340, row_rect.y + 17, 240, 20)
    if category == "accessibility" and key in ["screen_shake", "ui_size"]:
        return pygame.Rect(row_rect.right - 340, row_rect.y + 17, 240, 20)
    return None


def start_settings_drag(click_pos):
    global settings_dragging_slider
    settings_dragging_slider = None

    rows = []
    if settings_category == "audio":
        rows = [("music", SCREEN_H * 0.25 + 0 * 70), ("sfx", SCREEN_H * 0.25 + 1 * 70)]
    elif settings_category == "accessibility":
        rows = [("screen_shake", SCREEN_H * 0.25 + 0 * 70), ("ui_size", SCREEN_H * 0.25 + 1 * 70)]

    for key, y_pos in rows:
        s_rect = _slider_rect_for_category(settings_category, key, y_pos)
        if s_rect and s_rect.collidepoint(click_pos):
            settings_dragging_slider = (settings_category, key, s_rect)
            update_settings_drag(click_pos)
            break


def update_settings_drag(mouse_pos):
    global temp_settings, settings
    if not settings_dragging_slider:
        return

    category, key, s_rect = settings_dragging_slider
    ratio = (mouse_pos[0] - s_rect.x) / max(1, s_rect.width)
    ratio = max(0.0, min(1.0, ratio))

    if category == "audio":
        temp_settings["audio"][key] = int(ratio * 100)
        settings = _deepcopy_settings(temp_settings)
        save_settings(settings)
        apply_audio_runtime(settings)
    elif category == "accessibility":
        if key == "screen_shake":
            temp_settings["accessibility"][key] = int(ratio * 100)
        else:
            temp_settings["accessibility"][key] = int(60 + ratio * 40)
        settings = _deepcopy_settings(temp_settings)
        save_settings(settings)


def stop_settings_drag():
    global settings_dragging_slider
    settings_dragging_slider = None


if __name__ == "__main__":
    main()
