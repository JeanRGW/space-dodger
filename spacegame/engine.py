from __future__ import annotations

import math
import time
from typing import Callable

import pygame
from pygame.locals import (
    DOUBLEBUF,
    OPENGL,
    RESIZABLE,
    K_ESCAPE,
    K_LEFT,
    K_RIGHT,
    K_UP,
    K_DOWN,
    K_RETURN,
    K_SPACE,
    K_p,
    K_q,
    K_m,
    QUIT,
    VIDEORESIZE,
    KEYDOWN,
)

import leaderboard as lb

from .constants import (
    COLS,
    SCREEN_W,
    SCREEN_H,
    DIFFICULTY,
    COLLECTOR_DIFFICULTY,
    STATE_GAMEOVER,
    STATE_MENU,
    STATE_PAUSED,
    STATE_PLAYING,
    GAME_MODE_SURVIVAL,
    GAME_MODE_COLLECTOR,
)
from .gameplay import fire_shot, spawn_stars, update_shots, update_stars, spawn_collector_stars, update_collector_stars
from .rendering import Renderer
from .state import GameState


class Game:
    def __init__(self) -> None:
        self.state = GameState()
        self.renderer = Renderer(self.state)
        self.running = False
        self.load_leaderboard: Callable[[], None] = lb.load_leaderboard
        self.save_leaderboard: Callable[[], None] = lb.save_leaderboard
        self.qualifies_for_leaderboard: Callable[[str, int], bool] = lb.qualifies_for_leaderboard
        self.add_score_to_leaderboard: Callable[[str, str, int], None] = lb.add_score_to_leaderboard

    def run(self) -> None:
        pygame.init()
        self._create_window(self.state.window.width, self.state.window.height)
        self.renderer.initialize()
        self.renderer.load_moon_texture()
        self.load_leaderboard()
        clock = pygame.time.Clock()
        self.running = True
        last_time = time.time()
        while self.running:
            now = time.time()
            delta = now - last_time
            last_time = now
            self.state.spawn_timer += delta
            self._handle_events()
            self._update(delta)
            self._render()
            clock.tick(60)
        pygame.quit()

    def _create_window(self, width: int, height: int) -> None:
        pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption("Space Dodger v1.0a")

    def _handle_events(self) -> None:
        '''Tratar eventos do pygame e encaminhar entrada para handlers específicos.'''
        state = self.state
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == VIDEORESIZE:
                state.window.width, state.window.height = event.w, event.h
                self._create_window(event.w, event.h)
                self.renderer.resize(event.w, event.h)
            elif event.type == KEYDOWN:
                if state.game_state == STATE_MENU:
                    self._handle_menu_input(event)
                elif state.game_state == STATE_PLAYING:
                    self._handle_playing_input(event)
                elif state.game_state == STATE_PAUSED:
                    self._handle_pause_input(event)
                elif state.game_state == STATE_GAMEOVER:
                    self._handle_gameover_input(event)

    def _handle_menu_input(self, event) -> None:
        state = self.state
        menu = state.menu
        key = event.key

        # Exibindo leaderboard?
        if menu.show_leaderboard:
            if key in (K_ESCAPE, K_m):
                menu.show_leaderboard = False
            elif key in (K_RETURN, K_SPACE):
                menu.show_leaderboard = False
            elif key == K_LEFT:
                menu.difficulty_index = max(0, menu.difficulty_index - 1)
            elif key == K_RIGHT:
                menu.difficulty_index = min(len(menu.difficulty_names) - 1, menu.difficulty_index + 1)
            elif key == K_UP:
                menu.mode_index = max(0, menu.mode_index - 1)
            elif key == K_DOWN:
                menu.mode_index = min(len(menu.mode_names) - 1, menu.mode_index + 1)
            return
        
        # Menu principal
        if key == K_UP:
            menu.selected = max(0, menu.selected - 1)
        elif key == K_DOWN:
            menu.selected = min(len(menu.items) - 1, menu.selected + 1)
        # Seleção de modo
        elif key in (K_LEFT, K_RIGHT) and menu.selected == 1:
            if key == K_LEFT:
                menu.mode_index = max(0, menu.mode_index - 1)
            else:
                menu.mode_index = min(len(menu.mode_names) - 1, menu.mode_index + 1)
        # Seleção de dificuldade
        elif key in (K_LEFT, K_RIGHT) and menu.selected == 2:
            if key == K_LEFT:
                menu.difficulty_index = max(0, menu.difficulty_index - 1)
            else:
                menu.difficulty_index = min(len(menu.difficulty_names) - 1, menu.difficulty_index + 1)

        # Ações de menu
        elif key in (K_RETURN, K_SPACE):
            if menu.selected == 0:
                # Iniciar jogo
                self.state.game_mode = menu.mode_index
                self.state.leaderboard.last_played_difficulty = menu.difficulty_names[menu.difficulty_index]
                self.state.leaderboard.prompted = False
                self.state.reset()
                self.state.game_state = STATE_PLAYING
            elif menu.selected == 1:
                # Ciclar modo
                menu.mode_index = (menu.mode_index + 1) % len(menu.mode_names)
            elif menu.selected == 2:
                # Ciclar dificuldade
                menu.difficulty_index = (menu.difficulty_index + 1) % len(menu.difficulty_names)
            elif menu.selected == 3:
                # Mostrar leaderboard
                menu.show_leaderboard = True
            elif menu.selected == 4:
                # Sair
                self.running = False

    def _handle_playing_input(self, event) -> None:
        key = event.key
        player = self.state.player
        if key == K_LEFT:
            player.target_x -= 1
        elif key == K_RIGHT:
            player.target_x += 1
        elif key == K_SPACE and self.state.game_mode == GAME_MODE_SURVIVAL:
            fire_shot(self.state)
        elif key in (K_p, K_ESCAPE):
            self.state.menu.pause_selected = 0
            self.state.game_state = STATE_PAUSED

    def _handle_pause_input(self, event) -> None:
        key = event.key
        menu = self.state.menu
        if key == K_UP:
            menu.pause_selected = max(0, menu.pause_selected - 1)
        elif key == K_DOWN:
            menu.pause_selected = min(2, menu.pause_selected + 1)
        # Ações por cursor
        elif key in (K_RETURN, K_SPACE):
            if menu.pause_selected == 0:
                self.state.game_state = STATE_PLAYING
            elif menu.pause_selected == 1:
                self.state.game_state = STATE_MENU
            else:
                self.running = False

        # Ações por tecla direta
        elif key in (K_p, K_ESCAPE):
            self.state.game_state = STATE_PLAYING
        elif key == K_m:
            self.state.game_state = STATE_MENU
        elif key == K_q:
            self.running = False

    def _handle_gameover_input(self, event) -> None:
        key = event.key
        lb_state = self.state.leaderboard
        if lb_state.capturing_name:
            if key == pygame.K_BACKSPACE:
                lb_state.name_buffer = lb_state.name_buffer[:-1]
            elif key in (K_RETURN, pygame.K_KP_ENTER):
                final_name = lb_state.name_buffer.strip() or "Player"
                if lb_state.pending_difficulty:
                    score_value = int(self.state.time_alive) if self.state.game_mode == GAME_MODE_COLLECTOR else self.state.score
                    self.add_score_to_leaderboard(lb_state.pending_difficulty, final_name, score_value)
                    self.save_leaderboard()
                lb_state.capturing_name = False
                lb_state.pending_difficulty = None
            elif key == K_ESCAPE:
                lb_state.capturing_name = False
                lb_state.pending_difficulty = None
            else:
                ch = getattr(event, 'unicode', '')
                if ch and ch.isprintable() and len(lb_state.name_buffer) < 32:
                    lb_state.name_buffer += ch
        else:
            if key in (K_RETURN, K_SPACE):
                self.state.reset()
                self.state.game_state = STATE_PLAYING
            elif key == K_q:
                self.running = False
            elif key == K_m:
                self.state.game_state = STATE_MENU

    def _update(self, delta: float) -> None:
        state = self.state
        menu = state.menu
        if state.game_state == STATE_PLAYING:
            player = state.player
            player.target_x = max(0, min(COLS - 1, player.target_x))
            diff = player.target_x - player.x
            player.x = smooth_lerp(player.x, player.target_x, delta, 10)
            lateral = abs(player.target_x - player.x)
            desired_z = 12.0 - min(4.5, lateral * 2.0)
            v = diff / max(delta, 1e-6)
            look_ahead = max(-2.0, min(2.0, v * 0.02))
            desired_x = player.x + look_ahead
            desired_y = 3.0
            state.camera.x = smooth_lerp(state.camera.x, desired_x, delta, 10.0)
            state.camera.y = smooth_lerp(state.camera.y, desired_y, delta, 6.0)
            state.camera.z = smooth_lerp(state.camera.z, desired_z, delta, 6.0)
            difficulty_name = menu.difficulty_names[menu.difficulty_index]
            
            # Modos de jogo
            if state.game_mode == GAME_MODE_COLLECTOR:
                # Lógica do modo Collector
                cfg = COLLECTOR_DIFFICULTY[difficulty_name]
                if state.spawn_timer > cfg['spawn_interval']:
                    spawn_collector_stars(state, difficulty_name)
                    state.spawn_timer = 0
                alive = update_collector_stars(state, difficulty_name, delta)
                if not alive:
                    state.game_state = STATE_GAMEOVER
            else:
                # Lógica do modo Survival
                if state.spawn_timer > DIFFICULTY[difficulty_name]['spawn_interval']:
                    spawn_stars(state, difficulty_name)
                    state.spawn_timer = 0
                alive = update_stars(state, difficulty_name, delta)
                if not alive:
                    state.game_state = STATE_GAMEOVER
                update_shots(state, delta)
            
            state.time_alive += delta
        menu.anim += delta
        player = state.player
        player.shot_charge = min(1.0, player.shot_charge + delta / player.shot_cooldown)
        if player.shield_time > 0:
            player.shield_time = max(0.0, player.shield_time - delta)
        if state.effects.global_slow_time > 0:
            state.effects.global_slow_time = max(0.0, state.effects.global_slow_time - delta)
        state.effects.moon_angle += delta * 2
        if state.game_state == STATE_GAMEOVER and not state.leaderboard.prompted:
            difficulty = state.leaderboard.last_played_difficulty
            mode_suffix = '-Coletor' if state.game_mode == GAME_MODE_COLLECTOR else ''
            difficulty_key = difficulty + mode_suffix if difficulty else None
            
            # Score: coletor -> tempo vivo, survival -> pontos
            score_value = int(state.time_alive) if state.game_mode == GAME_MODE_COLLECTOR else state.score
            if difficulty_key and self.qualifies_for_leaderboard(difficulty_key, score_value):
                state.leaderboard.capturing_name = True
                state.leaderboard.name_buffer = ""
                state.leaderboard.pending_difficulty = difficulty_key
            state.leaderboard.prompted = True

    def _render(self) -> None:
        state = self.state
        if state.game_state == STATE_MENU:
            self.renderer.draw_menu_background()
            self.renderer.draw_menu_overlay(lb)
        elif state.game_state in (STATE_PAUSED, STATE_GAMEOVER):
            self.renderer.draw_scene()
            self.renderer.draw_menu_overlay(lb)
        else:
            self.renderer.draw_scene()
        pygame.display.flip()

# Suavizar movimento
def smooth_lerp(current: float, target: float, dt: float, speed: float) -> float:
    if dt <= 0:
        return target
    alpha = 1.0 - math.exp(-speed * dt)
    return current + (target - current) * alpha
