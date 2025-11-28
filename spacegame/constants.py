# grid e tela
COLS = 12
ROWS = 7
SCREEN_W = 800
SCREEN_H = 800

# estados do jogo
STATE_MENU = 0
STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_GAMEOVER = 3

# modos de jogo
GAME_MODE_SURVIVAL = 0
GAME_MODE_COLLECTOR = 1

# configurações de dificuldade
DIFFICULTY = {
    'Easy':  {'spawn_interval': 1.2, 'star_speed': 6.0, 'spawn_min': max(1, COLS//5), 'spawn_max': max(1, COLS//3)},
    'Normal':{'spawn_interval': 0.8, 'star_speed': 10.0, 'spawn_min': max(1, COLS//4), 'spawn_max': max(1, COLS//2)},
    'Hard':  {'spawn_interval': 0.7,'star_speed': 16.0, 'spawn_min': max(1, COLS//3), 'spawn_max': max(1, COLS)}
}

# dificuldades do modo coletor
COLLECTOR_DIFFICULTY = {
    'Easy':  {'spawn_interval': 2.0, 'star_speed': 7.0, 'stars_per_wave': 1, 'max_misses': 5},
    'Normal':{'spawn_interval': 1.5, 'star_speed': 9.0, 'stars_per_wave': 2, 'max_misses': 3},
    'Hard':  {'spawn_interval': 1.2, 'star_speed': 13.0, 'stars_per_wave': 2, 'max_misses': 2}
}

# escalas de renderização de modelos
MODEL_SCALE_SHIP = 1
MODEL_SCALE_OBJECT = 1

# índices das propriedades da lista de estrelas (compartilhados entre módulos)
STAR_X = 0
STAR_Y = 1
STAR_Z = 2
STAR_KIND = 3
STAR_SIZE = 4
STAR_R = 5
STAR_G = 6
STAR_B = 7
STAR_HP = 8
STAR_SPIN_ANGLE = 9
STAR_SPIN_SPEED = 10
