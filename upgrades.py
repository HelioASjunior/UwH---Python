import random


def pick_upgrades_with_synergy(pool, current_upgrades, unlocks, default_unlocks, evolutions, upgrade_tags, max_upgrade_level, k=3):
    """Seleciona upgrades levando em conta unlocks, limite de nível e sinergias."""

    available = [u for u in pool if u in unlocks or u in default_unlocks]

    for evo_name, evo_data in evolutions.items():
        if (
            evo_data["base"] in current_upgrades
            and evo_data["passive"] in current_upgrades
            and evo_name not in current_upgrades
            and evo_name not in available
        ):
            available.append(evo_name)

    filtered = [
        u for u in available
        if u not in current_upgrades or current_upgrades.count(u) < max_upgrade_level
    ]

    if not filtered:
        filtered = list(pool)

    k = min(k, len(filtered))

    synergy_picks = []
    for u in filtered:
        tags = upgrade_tags.get(u, set())
        for existing in current_upgrades:
            existing_tags = upgrade_tags.get(existing, set())
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


def get_upgrade_description(key, evolutions, all_upgrades_pool, upgrade_pool):
    """Retorna descrição segura para upgrade comum ou evolução."""
    if key in evolutions:
        return evolutions[key]["desc"]
    return all_upgrades_pool.get(key, upgrade_pool.get(key, "Sem descrição disponível."))
