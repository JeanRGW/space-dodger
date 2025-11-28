from __future__ import annotations

import random
from typing import List
from .constants import (
    STAR_X, STAR_Y, STAR_Z, STAR_KIND, STAR_SIZE, STAR_R, STAR_G, STAR_B,
    STAR_HP, STAR_SPIN_ANGLE, STAR_SPIN_SPEED
)

from .constants import COLS, DIFFICULTY, COLLECTOR_DIFFICULTY, GAME_MODE_COLLECTOR
from .state import GameState


def create_explosion(state: GameState, x: float, y: float, z: float) -> None:
    state.objects.explosions.append([x, y, z, 0.1, 0.0, 0.4])


# Configurações de spawn de objetos
MIN_SPAWN_GAP_X = 0.85
MIN_SPAWN_GAP_Z = 9.0
Z_SPAWN_RANGE = (-110.0, -40.0)
COLLECTOR_Z_SPAWN = -40.0


def spawn_stars(state: GameState, difficulty_name: str) -> None:
    cfg = DIFFICULTY.get(difficulty_name, DIFFICULTY['Normal'])
    stars_to_spawn = random.randint(cfg['spawn_min'], cfg['spawn_max'])
    for _ in range(stars_to_spawn):
        lane = random.randint(0, COLS - 1)
        x, z = _pick_spawn_slot(state, lane)
        kind = 'asteroid'
        r = random.random()
        if r < 0.08:
            kind = 'pickup'
        elif r < 0.3:
            kind = 'enemy'
        if kind == 'asteroid':
            size = random.uniform(0.5, 1.0)
            color = (0.5, 0.45, 0.35)
            hp = 1
        elif kind == 'enemy':
            size = random.uniform(0.34, 0.6)
            color = (1.0, 0.2, 0.45)
            hp = 1
        else:
            size = random.uniform(0.25, 0.45)
            color = (0.2, 1.0, 0.6)
            hp = 0
        spin_angle, spin_speed = _spin_profile(kind)
        state.objects.stars.append([x, 0, z, kind, size, color[0], color[1], color[2], hp, spin_angle, spin_speed])


def spawn_collector_stars(state: GameState, difficulty_name: str) -> None:
    cfg = COLLECTOR_DIFFICULTY.get(difficulty_name, COLLECTOR_DIFFICULTY['Normal'])
    stars_to_spawn = cfg['stars_per_wave']

    # Lista de estrelas ativas -> Evitar spawn na mesma linha
    active_positions: List[tuple[int, float]] = []
    for s in state.objects.stars:
        if s[STAR_KIND] == 'collector_star':
            active_positions.append((int(round(s[STAR_X])), s[STAR_Z]))

    player_lane = int(round(state.player.x))
    lanes = list(range(COLS))
    lanes.sort(key=lambda lane: abs(lane - player_lane))  # Priorizar linhas próximas ao jogador

    last_lane: int | None = None
    last_z = COLLECTOR_Z_SPAWN

    # Ajuste de separação:
    # base_sep: sepração mínima entre estrelas (z).
    # extra_sep: separação adicional máxima (escalada pela diferença de linha).
    base_sep = 8.0
    extra_sep = 34.0
    max_total_back = 260.0

    attempts = 0
    max_attempts = stars_to_spawn * 15
    spawned = 0
    while spawned < stars_to_spawn and attempts < max_attempts:
        attempts += 1

        # Preferir linhas próximas ao jogador
        if random.random() < 0.6:
            candidate_pool = lanes[:min(4, len(lanes))]
        else:
            candidate_pool = lanes
        if not candidate_pool:
            break
        lane = random.choice(candidate_pool)

        lane_diff = 0 if last_lane is None else abs(lane - last_lane)
        lane_factor = lane_diff / max(1, COLS - 1)
        scaled = lane_factor * lane_factor
        star_speed = COLLECTOR_DIFFICULTY.get(difficulty_name, COLLECTOR_DIFFICULTY['Normal'])['star_speed']
        speed_factor = star_speed / 10.0
        sep = base_sep + scaled * extra_sep * speed_factor

        sep = min(sep, base_sep + extra_sep)


        z = last_z if last_lane is None else last_z - sep
        if z < COLLECTOR_Z_SPAWN - max_total_back:

            z = COLLECTOR_Z_SPAWN - max_total_back

        z += random.uniform(-1.0, 1.0)

        conflict = False
        for act_lane, act_z in active_positions:
            if abs(z - act_z) < 6.0:
                conflict = True
                break
        if conflict:
            continue

        x = float(lane) + random.uniform(-0.15, 0.15)
        size = random.uniform(0.45, 0.55)
        color = (1.0, 0.9, 0.2)
        spin_angle = random.uniform(0.0, 360.0)
        spin_speed = random.uniform(40.0, 60.0)
        state.objects.stars.append([
            x, 0, z, 'collector_star', size,
            color[0], color[1], color[2], 0,
            spin_angle, spin_speed
        ])
        active_positions.append((lane, z))
        last_lane = lane
        last_z = z
        spawned += 1


def update_stars(state: GameState, difficulty_name: str, delta: float) -> bool:
    cfg = DIFFICULTY.get(difficulty_name, DIFFICULTY['Normal'])
    base_speed = cfg['star_speed']
    player = state.player
    new_stars: List[list] = []
    slow_factor = 0.5 if state.effects.global_slow_time > 0 else 1.0
    for star in state.objects.stars:
        kind = star[STAR_KIND]
        size = star[STAR_SIZE]
        move_factor = 1.2 if kind == 'enemy' else 1.0
        star_speed = base_speed * move_factor * slow_factor
        star[STAR_Z] += delta * star_speed
        if len(star) > STAR_SPIN_SPEED:
            star[STAR_SPIN_ANGLE] = (star[STAR_SPIN_ANGLE] + star[STAR_SPIN_SPEED] * delta) % 360
        z_hit_thresh = max(0.6, size * 1.0)
        x_hit_thresh = max(0.5, size * 0.7)
        if abs(star[STAR_X] - player.x) < x_hit_thresh and abs(star[STAR_Z] - player.z) < z_hit_thresh:
            if kind == 'pickup':
                _apply_pickup(state)
                create_explosion(state, star[STAR_X], star[STAR_Y], star[STAR_Z])
                state.score += 2
                continue
            if player.shield_time > 0:
                player.shield_time = 0
                create_explosion(state, player.x, 0.2, player.z)
                state.score += 5 if kind == 'enemy' else 2
                continue
            create_explosion(state, player.x, 0.2, player.z)
            return False
        if star[STAR_Z] < 8.0:
            new_stars.append(star)
    state.objects.stars = new_stars
    return True


def update_collector_stars(state: GameState, difficulty_name: str, delta: float) -> bool:
    cfg = COLLECTOR_DIFFICULTY.get(difficulty_name, COLLECTOR_DIFFICULTY['Normal'])
    base_speed = cfg['star_speed']
    player = state.player
    new_stars: List[list] = []
    for star in state.objects.stars:
        if star[STAR_KIND] != 'collector_star':
            continue
        size = star[STAR_SIZE]
        star[STAR_Z] += delta * base_speed
        if len(star) > STAR_SPIN_SPEED:
            star[STAR_SPIN_ANGLE] = (star[STAR_SPIN_ANGLE] + star[STAR_SPIN_SPEED] * delta) % 360
        z_hit_thresh = max(0.6, size * 1.2)
        x_hit_thresh = max(0.6, size * 1.0)
        if abs(star[STAR_X] - player.x) < x_hit_thresh and abs(star[STAR_Z] - player.z) < z_hit_thresh:
            create_explosion(state, star[STAR_X], star[STAR_Y], star[STAR_Z])
            state.score += 1
            continue
        if star[STAR_Z] > player.z + 2.0:
            state.missed_stars += 1
            if state.missed_stars >= cfg['max_misses']:
                return False
            continue
        if star[STAR_Z] < player.z + 15.0:
            new_stars.append(star)
    state.objects.stars = new_stars
    return True


def fire_shot(state: GameState) -> None:
    if state.player.shot_charge < 1.0:
        return
    state.player.shot_charge = 0.0
    state.objects.shots.append([state.player.x, 0, state.player.z])


def update_shots(state: GameState, delta: float) -> None:
    new_shots = []
    for shot in state.objects.shots:
        shot[2] -= delta * 20
        if shot[2] <= -75.0:
            continue
        hit = None
        for star in state.objects.stars:
            size = star[4]
            if abs(star[0] - shot[0]) < max(0.2, size - 0.1) and abs(star[2] - shot[2]) < 0.2 + delta * 20:
                hit = star
                break
        if hit:
            kind = hit[3]
            if kind == 'pickup':
                _apply_pickup(state)
                create_explosion(state, hit[0], hit[1], hit[2])
                state.objects.stars.remove(hit)
            else:
                if len(hit) > 8 and hit[8] > 1:
                    hit[8] -= 1
                else:
                    create_explosion(state, hit[0], hit[1], hit[2])
                    state.objects.stars.remove(hit)
                    if kind == 'enemy':
                        state.score += 15
                        if random.random() < 0.25:
                            px, pz = _resolve_spacing(state, hit[0], hit[2] - 2.0)
                            size = random.uniform(0.25, 0.4)
                            color = (0.2, 1.0, 0.6)
                            spin_angle, spin_speed = _spin_profile('pickup')
                            state.objects.stars.append([px, 0, pz, 'pickup', size, color[0], color[1], color[2], 0, spin_angle, spin_speed])
                    else:
                        state.score += 5
        else:
            new_shots.append(shot)
    state.objects.shots = new_shots


def _apply_pickup(state: GameState) -> None:
    r = random.random()
    if r < 0.5:
        state.player.shield_time = max(state.player.shield_time, 5.0)
    elif r < 0.85:
        state.effects.global_slow_time = max(state.effects.global_slow_time, 6.0)
    else:
        state.player.shot_charge = 1.0


def _pick_spawn_slot(state: GameState, lane: int) -> tuple[float, float]:
    for attempt in range(8):
        x = float(lane) + random.uniform(-0.18, 0.18)
        z = random.uniform(*Z_SPAWN_RANGE)
        if _position_is_clear(state, x, z):
            return x, z
    
    x = float(lane) + random.uniform(-0.22, 0.22)
    z = random.uniform(Z_SPAWN_RANGE[0] - 10.0, Z_SPAWN_RANGE[1])
    return _resolve_spacing(state, x, z)


def _position_is_clear(state: GameState, x: float, z: float) -> bool:
    for obj in state.objects.stars:
        if abs(obj[0] - x) < MIN_SPAWN_GAP_X and abs(obj[2] - z) < MIN_SPAWN_GAP_Z:
            return False
    return True


def _resolve_spacing(state: GameState, x: float, z: float, step: float = 4.0) -> tuple[float, float]:
    for _ in range(10):
        if _position_is_clear(state, x, z):
            return x, z
        z -= step
    return x, z


def _spin_profile(kind: str) -> tuple[float, float]:
    base_angle = random.uniform(0.0, 360.0)
    if kind == 'asteroid':
        speed = random.uniform(-70.0, 70)
    elif kind == 'enemy':
        speed = 0.0
    elif kind == 'pickup':
        speed = random.uniform(20.0, 35.0)
    else:
        speed = random.uniform(8.0, 16.0)
    return base_angle, speed
