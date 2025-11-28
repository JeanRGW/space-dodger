"""Dataclasses describing the mutable state of the game."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .constants import COLS, SCREEN_W, SCREEN_H, STATE_MENU


Vec3 = Tuple[float, float, float]


@dataclass
class PlayerState:
    x: float = COLS / 2
    z: float = 1.0
    speed: float = 8.0
    target_x: float = COLS / 2
    shot_charge: float = 1.0
    shot_cooldown: float = 5.0
    shield_time: float = 0.0


@dataclass
class EffectsState:
    global_slow_time: float = 0.0
    moon_angle: float = 0.0
    background_stars: List[Tuple[float, float, float, float]] = field(default_factory=list)


@dataclass
class CameraState:
    x: float = COLS / 2
    y: float = 3.0
    z: float = 12.0


@dataclass
class MenuState:
    items: Tuple[str, ...] = ("Iniciar jogo", "Modo: {}", "Dificuldade: {}", "Leaderboard", "Sair")
    selected: int = 0
    mode_names: Tuple[str, ...] = ("Sobrevivência", "Coletor")
    mode_index: int = 0
    difficulty_names: Tuple[str, ...] = ("Fácil", "Normal", "Difícil")
    difficulty_index: int = 1
    anim: float = 0.0
    show_leaderboard: bool = False
    pause_selected: int = 0


@dataclass
class LeaderboardState:
    capturing_name: bool = False
    name_buffer: str = ""
    pending_difficulty: str | None = None
    last_played_difficulty: str | None = None
    prompted: bool = False


@dataclass
class GameObjects:
    stars: List[list] = field(default_factory=list)
    shots: List[List[float]] = field(default_factory=list)
    explosions: List[list] = field(default_factory=list)


@dataclass
class WindowState:
    width: int = SCREEN_W
    height: int = SCREEN_H


@dataclass
class GameState:
    player: PlayerState = field(default_factory=PlayerState)
    effects: EffectsState = field(default_factory=EffectsState)
    camera: CameraState = field(default_factory=CameraState)
    menu: MenuState = field(default_factory=MenuState)
    leaderboard: LeaderboardState = field(default_factory=LeaderboardState)
    objects: GameObjects = field(default_factory=GameObjects)
    window: WindowState = field(default_factory=WindowState)
    score: int = 0
    time_alive: float = 0.0
    spawn_timer: float = 0.0
    moon_texture: int | None = None
    game_state: int = STATE_MENU
    game_mode: int = 0  # 0 -> Survival, 1 -> Coletor
    missed_stars: int = 0  # p/ modo coletor
    capturing_name: bool = False 

    def reset(self) -> None:
        self.objects.stars.clear()
        self.objects.shots.clear()
        self.objects.explosions.clear()
        self.score = 0
        self.time_alive = 0.0
        self.missed_stars = 0
        self.player.x = COLS / 2
        self.player.target_x = self.player.x
        self.player.shield_time = 0.0
        self.player.shot_charge = 1.0
        self.effects.global_slow_time = 0.0
        self.spawn_timer = 0.0
        self.leaderboard.capturing_name = False
        self.leaderboard.name_buffer = ""
        self.leaderboard.pending_difficulty = None
        self.leaderboard.prompted = False
