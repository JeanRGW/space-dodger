from __future__ import annotations

import math
import random
import time
from typing import Dict, Optional

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import glutInit, glutBitmapCharacter, GLUT_BITMAP_HELVETICA_18
from PIL import Image

from .constants import (
    COLS,
    MODEL_SCALE_OBJECT,
    MODEL_SCALE_SHIP,
    STATE_GAMEOVER,
    STATE_MENU,
    STATE_PAUSED,
    GAME_MODE_COLLECTOR,
    COLLECTOR_DIFFICULTY,
)
from .constants import (
    STAR_X, STAR_Y, STAR_Z, STAR_KIND, STAR_SIZE, STAR_R, STAR_G, STAR_B, STAR_SPIN_ANGLE, STAR_SPIN_SPEED
)
from .state import GameState

try:
    from assets import load_texture as load_texture_from_file
except Exception: 
    load_texture_from_file = None

glutInit()


CUBE_FACES = [
    ((0, 0, 1), ((-0.5, -0.5, 0.5), (0.5, -0.5, 0.5), (0.5, 0.5, 0.5), (-0.5, 0.5, 0.5))),
    ((0, 0, -1), ((-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5), (0.5, -0.5, -0.5))),
    ((-1, 0, 0), ((-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5), (-0.5, 0.5, -0.5))),
    ((1, 0, 0), ((0.5, -0.5, -0.5), (0.5, 0.5, -0.5), (0.5, 0.5, 0.5), (0.5, -0.5, 0.5))),
    ((0, 1, 0), ((-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5), (0.5, 0.5, -0.5))),
    ((0, -1, 0), ((-0.5, -0.5, -0.5), (0.5, -0.5, -0.5), (0.5, -0.5, 0.5), (-0.5, -0.5, 0.5))),
]

STAR_MAIN_FAN = [] 
STAR_GLOW_FAN = []  
for i in range(11):  
    ang = math.radians(i * 36.0)
    r_main = 1.0 if i % 2 == 0 else 0.4
    r_glow = 1.4 if i % 2 == 0 else 0.6
    STAR_MAIN_FAN.append((r_main * math.cos(ang), r_main * math.sin(ang)))
    STAR_GLOW_FAN.append((r_glow * math.cos(ang), r_glow * math.sin(ang)))


class Renderer:

    def __init__(self, state: GameState) -> None:
        self.state = state
        self.model_lists: Dict[str, int] = {}

    # ------------------------------------------------------------------
    # OpenGL / Texturas
    # ------------------------------------------------------------------
    def initialize(self) -> None:
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

        glLightfv(GL_LIGHT0, GL_POSITION, [COLS / 2, 5.0, 5.0, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT,  [0.1, 0.1, 0.1, 1.0])

        glClearColor(0, 0, 0, 1)
        self.resize(self.state.window.width, self.state.window.height)
        self._generate_background_stars()
        self._create_model_display_lists()

    def resize(self, width: int, height: int) -> None:
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = max(0.001, float(width) / max(1.0, height))
        gluPerspective(60, aspect, 0.1, 100)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_MODELVIEW)

    def load_moon_texture(self, path: str = "moon.jpg") -> None:
        self.state.moon_texture = self._load_texture(path)

    def _load_texture(self, path: str) -> int:
        if load_texture_from_file:
            try:
                return load_texture_from_file(path)
            except Exception:
                pass
        img = Image.open(path)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img_data = img.convert("RGB").tobytes()
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, img.width, img.height, 0,
                     GL_RGB, GL_UNSIGNED_BYTE, img_data)
        return texture_id

    def _generate_background_stars(self) -> None:
        self.state.effects.background_stars.clear()
        for _ in range(400):
            theta = random.random() * 2 * math.pi
            phi = random.random() * math.pi
            r = random.uniform(60, 250)
            x = r * math.sin(phi) * math.cos(theta)
            y = r * math.cos(phi)
            z = r * math.sin(phi) * math.sin(theta)
            self.state.effects.background_stars.append((x, y, z, random.uniform(0.5, 1.2)))

    # ------------------------------------------------------------------
    # Modelos 3D
    # ------------------------------------------------------------------
    def _emit_unit_cube(self) -> None:
        glBegin(GL_QUADS)
        for normal, face in CUBE_FACES:
            glNormal3f(*normal)
            for vertex in face:
                glVertex3f(*vertex)
        glEnd()

    def _create_model_display_lists(self) -> None:
        self.model_lists.clear()
        # Nave
        ship_list = glGenLists(1)
        glNewList(ship_list, GL_COMPILE)
        glPushMatrix()
        glScalef(0.32, 0.22, 1.4)
        self._emit_unit_cube()
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.0, 0.05, -0.85)
        glScalef(0.18, 0.16, 0.35)
        self._emit_unit_cube()
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.0, 0.12, -0.45)
        glScalef(0.26, 0.2, 0.45)
        self._emit_unit_cube()
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.0, -0.18, -0.15)
        glScalef(0.22, 0.1, 0.8)
        self._emit_unit_cube()
        glPopMatrix()
        for x_dir in (-0.32, 0.32):
            glPushMatrix()
            glTranslatef(x_dir, -0.04, -0.2)
            glScalef(0.18, 0.06, 0.95)
            self._emit_unit_cube()
            glPopMatrix()
        for x_dir in (-0.28, 0.28):
            glPushMatrix()
            glTranslatef(x_dir, 0.14, -0.55)
            glScalef(0.08, 0.2, 0.35)
            self._emit_unit_cube()
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0.0, 0.28, -0.1)
        glScalef(0.12, 0.4, 0.55)
        self._emit_unit_cube()
        glPopMatrix()
        for offset in (-0.14, 0.14):
            glPushMatrix()
            glTranslatef(offset, -0.06, 0.82)
            glScalef(0.15, 0.15, 0.32)
            self._emit_unit_cube()
            glPopMatrix()
        glEndList()
        self.model_lists['ship'] = ship_list

        # Asteroide
        ast_list = glGenLists(1)
        glNewList(ast_list, GL_COMPILE)
        chunk_specs = [
            (0.0, 0.0, 0.0, 0.75),
            (-0.35, 0.25, -0.15, 0.55),
            (0.4, -0.15, -0.25, 0.5),
            (0.0, -0.3, 0.35, 0.45),
        ]
        for tx, ty, tz, scale in chunk_specs:
            glPushMatrix()
            glTranslatef(tx, ty, tz)
            glRotatef(tx * 60 + tz * 30, 0.3, 1.0, 0.2)
            glScalef(scale, scale * 1.1, scale)
            self._emit_unit_cube()
            glPopMatrix()
        glEndList()
        self.model_lists['asteroid'] = ast_list

        # Inimigo
        enemy_list = glGenLists(1)
        glNewList(enemy_list, GL_COMPILE)
        glPushMatrix()
        glScalef(0.32, 0.24, 1.35)
        self._emit_unit_cube()
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.0, 0.02, -1.05)
        glScalef(0.12, 0.14, 0.45)
        self._emit_unit_cube()
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.0, 0.16, -0.45)
        glScalef(0.24, 0.24, 0.5)
        self._emit_unit_cube()
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.0, -0.22, -0.15)
        glScalef(0.26, 0.14, 0.8)
        self._emit_unit_cube()
        glPopMatrix()
        for x_dir in (-0.3, 0.3):
            glPushMatrix()
            glTranslatef(x_dir, 0.05, -0.15)
            glRotatef(18 * x_dir, 0.0, 0.0, 1.0)
            glScalef(0.1, 0.5, 0.95)
            self._emit_unit_cube()
            glPopMatrix()
        for offset in (-0.12, 0.12):
            glPushMatrix()
            glTranslatef(offset, 0.32, 0.1)
            glScalef(0.08, 0.35, 0.6)
            self._emit_unit_cube()
            glPopMatrix()
        for offset in (-0.2, 0.2):
            glPushMatrix()
            glTranslatef(offset, -0.04, 0.72)
            glScalef(0.16, 0.18, 0.5)
            self._emit_unit_cube()
            glPopMatrix()
            glPushMatrix()
            glTranslatef(offset, -0.02, 0.97)
            glScalef(0.12, 0.12, 0.18)
            self._emit_unit_cube()
            glPopMatrix()
        for offset in (-0.38, 0.38):
            glPushMatrix()
            glTranslatef(offset, 0.0, -0.2)
            glScalef(0.08, 0.08, 0.4)
            self._emit_unit_cube()
            glPopMatrix()
        glEndList()
        self.model_lists['enemy'] = enemy_list

    # ------------------------------------------------------------------
    # Desenho da cena
    # ------------------------------------------------------------------
    def draw_scene(self) -> None:
        state = self.state
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        player = state.player
        cam = state.camera
        gluLookAt(cam.x, cam.y, cam.z, player.x, 0.5, player.z - 6.0, 0, 1, 0)
        self._draw_background_stars()
        self._draw_moon(state.effects.moon_angle)
        if state.game_mode != GAME_MODE_COLLECTOR:
            self._draw_charge_ui()
        self.draw_ship(player.x, 0.2, player.z)
        if player.shield_time > 0:
            self._draw_player_shield()
        for star in state.objects.stars:
            x, y, z = star[STAR_X], star[STAR_Y], star[STAR_Z]
            kind = star[STAR_KIND]
            size = star[STAR_SIZE]
            color = (star[STAR_R], star[STAR_G], star[STAR_B])
            spin_angle = star[STAR_SPIN_ANGLE] if len(star) > STAR_SPIN_SPEED else None
            if kind == 'collector_star':
                self._draw_collector_star(x, y, z, size, color, spin_angle)
            elif kind == 'pickup':
                self._draw_pickup(x, y, z, size, color)
            elif kind == 'enemy':
                self.draw_enemy(x, y, z, size, color)
            else:
                self.draw_asteroid(x, y, z, size, color, spin_angle)
        for shot in state.objects.shots:
            self._draw_cube(shot[0], shot[1], shot[2], size=0.1, color=(0, 1, 1))
        self._draw_explosions(1 / 60)
        if state.effects.global_slow_time > 0:
            self._draw_slow_overlay()
        self._draw_hud()

    def draw_menu_background(self) -> None:
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        gluLookAt(0, 2.5, 26, 0, 0, 0, 0, 1, 0)
        self._draw_background_stars()
        self._draw_far_moon()

    # ------------------------------------------------------------------
    # Rederização de objetos
    # ------------------------------------------------------------------
    def draw_ship(self, x: float, y: float, z: float) -> None:
        glPushMatrix()
        glTranslatef(x, y, z)
        glScalef(MODEL_SCALE_SHIP, MODEL_SCALE_SHIP, MODEL_SCALE_SHIP)
        glMaterialfv(GL_FRONT, GL_AMBIENT, [0.18, 0.18, 0.2, 1.0])
        glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.6, 0.58, 0.62, 1.0])
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.8, 0.85, 0.9, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 80.0)
        ship_list = self.model_lists.get('ship')
        if ship_list:
            glCallList(ship_list)
        glPopMatrix()

    def draw_asteroid(self, x: float, y: float, z: float, size: float, color,
                      spin_angle: Optional[float] = None) -> None:
        glPushMatrix()
        glTranslatef(x, y, z)
        spin = (spin_angle if spin_angle is not None else (x * 6.0 + z * 1.2)) % 360
        glRotatef(spin, 0.1, 1.0, 0.05)
        scale = size * MODEL_SCALE_OBJECT
        glScalef(scale, scale, scale)
        glMaterialfv(GL_FRONT, GL_AMBIENT, [0.15 * color[0], 0.15 * color[1], 0.15 * color[2], 1.0])
        glMaterialfv(GL_FRONT, GL_DIFFUSE, [0.9 * color[0], 0.9 * color[1], 0.9 * color[2], 1.0])
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.05, 0.05, 0.05, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 6.0)
        ast_list = self.model_lists.get('asteroid')
        if ast_list:
            glCallList(ast_list)
        glPopMatrix()

    def draw_enemy(self, x: float, y: float, z: float, size: float, color) -> None:
        glPushMatrix()
        glTranslatef(x, y, z)
        scale = size * MODEL_SCALE_OBJECT * 1.18
        glScalef(scale, scale, scale)
        core_r = min(1.0, max(0.85, color[0]))
        core_g = min(1.0, color[1] * 0.7 + 0.1)
        core_b = min(1.0, color[2] * 0.6 + 0.15)
        glow = [core_r * 0.55, core_g * 0.4, core_b * 0.8, 1.0]
        glMaterialfv(GL_FRONT, GL_AMBIENT, [core_r * 0.6, core_g * 0.3, core_b * 0.4, 1.0])
        glMaterialfv(GL_FRONT, GL_DIFFUSE, [core_r, core_g, core_b, 1.0])
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.95, 0.3, 0.5, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 90.0)
        glMaterialfv(GL_FRONT, GL_EMISSION, glow)
        enemy_list = self.model_lists.get('enemy')
        if enemy_list:
            glCallList(enemy_list)
        glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1])
        glPopMatrix()

    def _draw_pickup(self, x, y, z, size, color) -> None:
        self._draw_cube(x, y, z, size=size * 0.8, color=color)
        self._draw_cube(x, y + 0.1, z, size=size * 0.4, color=(1, 1, 1))

    # Desenho das estrelas 
    def _draw_collector_star(self, x, y, z, size, color, spin_angle) -> None:
        glPushMatrix()
        glTranslatef(x, y, z)
        if spin_angle is not None:
            glRotatef(spin_angle, 0, 1, 0)
        
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        
        scale = size * 0.9
        glScalef(scale, scale, scale)
        
        glColor4f(color[0], color[1], color[2], 0.9)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, 0, 0)
        for vx, vy in STAR_MAIN_FAN:
            glVertex3f(vx, vy, 0)
        glEnd()
        
        glColor4f(color[0], color[1], color[2], 0.3)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, 0, 0)
        for vx, vy in STAR_GLOW_FAN:
            glVertex3f(vx, vy, 0)
        glEnd()
        
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glPopMatrix()

    def _draw_cube(self, x, y, z, size=0.4, color=(1, 1, 1)) -> None:
        glPushMatrix()
        glDisable(GL_LIGHTING)
        glTranslatef(x, y, z)
        glScalef(size, size, size)
        glMaterialfv(GL_FRONT, GL_EMISSION, [color[0], color[1], color[2], 1.0])
        glColor3f(*color)
        glBegin(GL_QUADS)
        glVertex3f(-0.5, -0.5,  0.5)
        glVertex3f( 0.5, -0.5,  0.5)
        glVertex3f( 0.5,  0.5,  0.5)
        glVertex3f(-0.5,  0.5,  0.5)
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(-0.5,  0.5, -0.5)
        glVertex3f( 0.5,  0.5, -0.5)
        glVertex3f( 0.5, -0.5, -0.5)
        glVertex3f(-0.5,  0.5, -0.5)
        glVertex3f(-0.5,  0.5,  0.5)
        glVertex3f( 0.5,  0.5,  0.5)
        glVertex3f( 0.5,  0.5, -0.5)
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f( 0.5, -0.5, -0.5)
        glVertex3f( 0.5, -0.5,  0.5)
        glVertex3f(-0.5, -0.5,  0.5)
        glVertex3f( 0.5, -0.5, -0.5)
        glVertex3f( 0.5,  0.5, -0.5)
        glVertex3f( 0.5,  0.5,  0.5)
        glVertex3f( 0.5, -0.5,  0.5)
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(-0.5, -0.5,  0.5)
        glVertex3f(-0.5,  0.5,  0.5)
        glVertex3f(-0.5,  0.5, -0.5)
        glEnd()
        glMaterialfv(GL_FRONT, GL_EMISSION, [0, 0, 0, 1])
        glEnable(GL_LIGHTING)
        glPopMatrix()

    # ------------------------------------------------------------------
    # Fundo e Ambiente
    # ------------------------------------------------------------------
    def _draw_moon(self, angle: float) -> None:
        state = self.state
        glPushMatrix()
        glTranslatef(COLS / 2, -105.0, 0)
        glRotatef(angle, 1, 0, 0)
        glRotatef(state.player.x * -0.4, 0, 0, 1)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.05, 0.05, 0.05, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 8.0)
        glColor3f(1, 1, 1)
        if state.moon_texture:
            glBindTexture(GL_TEXTURE_2D, state.moon_texture)
        quad = gluNewQuadric()
        gluQuadricTexture(quad, GL_TRUE)
        gluSphere(quad, 100, 50, 50)
        gluDeleteQuadric(quad)
        glPopMatrix()

    def _draw_background_stars(self) -> None:
        state = self.state
        glPushMatrix()
        cam = state.camera
        glTranslatef(cam.x, cam.y, cam.z)
        glDisable(GL_LIGHTING)
        glPointSize(3.5) 
        glBegin(GL_POINTS)
        t = time.time()
        for sx, sy, sz, intensity in state.effects.background_stars:
            tw = 0.5 + 0.5 * math.sin((sx + sy + sz) * 0.01 + t * 3.0)
            c = max(0.1, min(1.0, intensity * tw))
            glColor3f(c, c, c)
            glVertex3f(sx, sy, sz)
        glEnd()
        glEnable(GL_LIGHTING)
        glPopMatrix()

    def _draw_far_moon(self) -> None:
        glPushMatrix()
        glTranslatef(COLS / 2, 34.0, -55.0)
        glRotatef(self.state.effects.moon_angle * 0.25, 0, 1, 0)
        if self.state.moon_texture:
            glBindTexture(GL_TEXTURE_2D, self.state.moon_texture)
        glEnable(GL_TEXTURE_2D)
        glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [0.9, 0.9, 0.95, 1.0])
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0.06, 0.06, 0.08, 1.0])
        glMaterialf(GL_FRONT, GL_SHININESS, 12.0)
        quad = gluNewQuadric()
        gluQuadricTexture(quad, GL_TRUE)
        gluSphere(quad, 16, 30, 30)
        gluDeleteQuadric(quad)
        glPopMatrix()

    def _draw_player_shield(self) -> None:
        player = self.state.player
        glPushMatrix()
        glTranslatef(player.x, 0.2, player.z)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        glDisable(GL_LIGHTING)
        alpha = max(0.15, min(0.6, (player.shield_time / 5.0) * 0.5 + 0.15 * math.sin(time.time() * 8.0)))
        glColor4f(0.2, 0.85, 1.0, alpha)
        quad = gluNewQuadric()
        gluSphere(quad, 0.9, 18, 18)
        gluDeleteQuadric(quad)
        glEnable(GL_LIGHTING)
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glPopMatrix()

    def _draw_explosions(self, delta: float) -> None:
        explosions = self.state.objects.explosions
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        to_remove = []
        for e in explosions:
            x, y, z, size, life, maxlife = e
            e[4] += delta
            e[3] += delta * 4
            alpha = 1.0 - (e[4] / maxlife)
            if alpha < 0:
                alpha = 0
            glColor4f(1.0, 0.8, 0.2, alpha)
            glPushMatrix()
            glTranslatef(x, y, z)
            glScalef(size, size, size)
            glBegin(GL_QUADS)
            glVertex3f(-1, -1, 0)
            glVertex3f(1, -1, 0)
            glVertex3f(1, 1, 0)
            glVertex3f(-1, 1, 0)
            glEnd()
            glPopMatrix()
            if e[4] >= maxlife:
                to_remove.append(e)
        for e in to_remove:
            explosions.remove(e)
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)

    def _draw_slow_overlay(self) -> None:
        width, height = self.state.window.width, self.state.window.height
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, width, height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        t = time.time()
        slow = self.state.effects.global_slow_time
        alpha = min(0.6, (slow / 6.0) * 0.6 + 0.05 * math.sin(t * 6.0))
        glColor4f(0.05, 0.2, 0.5, alpha)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(width, 0)
        glVertex2f(width, height)
        glVertex2f(0, height)
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_LIGHTING)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def _draw_hud(self) -> None:
        width, height = self.state.window.width, self.state.window.height
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, width, height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glColor3f(1, 0, 0)
        menu = self.state.menu
        
        if self.state.game_mode == GAME_MODE_COLLECTOR:
            difficulty_name = menu.difficulty_names[menu.difficulty_index]
            max_misses = COLLECTOR_DIFFICULTY[difficulty_name]['max_misses']
            hud_text = f"Tempo: {int(self.state.time_alive)}s  Estrelas: {self.state.score}  Perdidos: {self.state.missed_stars}/{max_misses}  Dif.: {difficulty_name}"
        else:
            hud_text = f"Pontuação: {self.state.score}  Tempo: {int(self.state.time_alive)}s  Dif.: {menu.difficulty_names[menu.difficulty_index]}"
        
        glRasterPos2f(8, height - 18)
        for ch in hud_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def _draw_charge_ui(self) -> None:
        width, height = self.state.window.width, self.state.window.height
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, width, height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        bar_x, bar_y, bar_w, bar_h = 20, 20, 200, 20
        glColor3f(0.1, 0.1, 0.1)
        glBegin(GL_QUADS)
        glVertex2f(bar_x, bar_y)
        glVertex2f(bar_x + bar_w, bar_y)
        glVertex2f(bar_x + bar_w, bar_y + bar_h)
        glVertex2f(bar_x, bar_y + bar_h)
        glEnd()
        glColor3f(0.0, 1.0, 1.0)
        width_fill = bar_w * self.state.player.shot_charge
        glBegin(GL_QUADS)
        glVertex2f(bar_x, bar_y)
        glVertex2f(bar_x + width_fill, bar_y)
        glVertex2f(bar_x + width_fill, bar_y + bar_h)
        glVertex2f(bar_x, bar_y + bar_h)
        glEnd()
        glColor3f(1, 1, 1)
        glRasterPos2f(bar_x + 4, bar_y + (bar_h // 2) + 4)
        for ch in "CARGA":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    # ------------------------------------------------------------------
    # Overlay do menu
    # ------------------------------------------------------------------
    def draw_menu_overlay(self, leaderboard_module) -> None:
        width, height = self.state.window.width, self.state.window.height
        menu = self.state.menu
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, width, height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.03, 0.03, 0.06, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(width, 0)
        glVertex2f(width, height)
        glVertex2f(0, height)
        glEnd()
        glColor3f(1, 1, 1)
        title = "SPACE DODGER"
        center_x = width / 2
        title_x = center_x - 120
        title_y = int(height * 0.12)
        glRasterPos2f(title_x - 2, title_y - 2)
        for ch in title:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        glRasterPos2f(title_x, title_y)
        for ch in title:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        authors = "por JeanRGW & QuatiGKT"
        glColor3f(0.8, 0.8, 0.9)
        glRasterPos2f(center_x - 80, title_y + 28)
        for ch in authors:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        state = self.state
        if state.game_state == STATE_MENU:
            if state.menu.show_leaderboard:
                self._draw_leaderboard(center_x, height, leaderboard_module)
            else:
                self._draw_menu_entries(center_x, height)
        elif state.game_state == STATE_PAUSED:
            self._draw_pause_menu(center_x, height)
        elif state.game_state == STATE_GAMEOVER:
            self._draw_gameover_overlay(center_x, height)
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def _draw_leaderboard(self, center_x: float, height: int, leaderboard_module) -> None:
        menu = self.state.menu
        difficulty_name = menu.difficulty_names[menu.difficulty_index]
        mode_name = menu.mode_names[menu.mode_index]
        lb_key = difficulty_name + ("-Coletor" if mode_name.lower().startswith("coletor") else "")
        glColor3f(1.0, 0.95, 0.6)
        glRasterPos2f(center_x - 180, int(height * 0.24))
        header = f"LEADERBOARD - {mode_name} / {difficulty_name}" if mode_name != 'Sobrevivência' else f"LEADERBOARD - {difficulty_name}"
        for ch in header:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        entries = leaderboard_module.get_leaderboard(lb_key)
        base_y = int(height * 0.32)
        if len(entries) == 0:
            glColor3f(0.8, 0.8, 0.85)
            glRasterPos2f(center_x - 120, base_y)
            for ch in "Sem registros ainda.":
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        else:
            for i, entry in enumerate(entries):
                y = base_y + i * 36
                glColor3f(0.95 if i < 3 else 0.9, 0.9, 0.7)
                glRasterPos2f(center_x - 140, y)
                text = f"{i+1:>2}. {entry['name'][:18]:18}  {entry['score']:>5}"
                for ch in text:
                    glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        glColor3f(0.7, 0.7, 0.85)
        glRasterPos2f(center_x - 180, base_y + 11 * 36)
        hint = "ESQ/DIR: Dificuldade  CIMA/BAIXO: Modo  Esc/Enter: Fechar"
        for ch in hint:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    def _draw_menu_entries(self, center_x: float, height: int) -> None:
        menu = self.state.menu
        for idx, item in enumerate(menu.items):
            if '{}' in item:
                if 'Modo' in item:
                    text = item.format(menu.mode_names[menu.mode_index])
                elif 'Dificuldade' in item:
                    text = item.format(menu.difficulty_names[menu.difficulty_index])
                else:
                    text = item
            else:
                text = item
            y = int(height * 0.33) + idx * 56
            is_selected = idx == menu.selected
            color = (1.0, 1.0, 0.2) if is_selected else (0.85, 0.85, 0.85)
            glColor3f(*color)
            menu_x = center_x - 60
            glRasterPos2f(menu_x, y)
            for ch in text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
            if is_selected:
                offset = 8.0 * math.sin(menu.anim * 6.0)
                cx = menu_x - 40 + offset
                cy = y - 6
                glColor3f(1.0, 0.9, 0.2)
                glBegin(GL_TRIANGLES)
                glVertex2f(cx + 12, cy)
                glVertex2f(cx, cy - 6)
                glVertex2f(cx, cy + 6)
                glEnd()

    def _draw_pause_menu(self, center_x: float, height: int) -> None:
        options = ["Continuar (P / Esc)", "Menu Principal (M)", "Sair (Q)"]
        glColor3f(1.0, 0.9, 0.4)
        glRasterPos2f(center_x - 40, height * 0.26)
        for ch in "PAUSADO":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        opt_x = center_x - 80
        base_y = int(height * 0.32)
        for i, text in enumerate(options):
            y = base_y + i * 48
            is_selected = (i == self.state.menu.pause_selected)
            color = (1.0, 0.95, 0.6) if is_selected else (0.8, 0.8, 0.85)
            glColor3f(*color)
            glRasterPos2f(opt_x, y)
            for ch in text:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
            if is_selected:
                offset = 6.0 * math.sin(self.state.menu.anim * 6.0)
                cx = opt_x - 40 + offset
                cy = y - 6
                glColor3f(1.0, 0.85, 0.2)
                glBegin(GL_TRIANGLES)
                glVertex2f(cx + 12, cy)
                glVertex2f(cx, cy - 6)
                glVertex2f(cx, cy + 6)
                glEnd()

    def _draw_gameover_overlay(self, center_x: float, height: int) -> None:
        lb_state = self.state.leaderboard
        if lb_state.capturing_name:
            glColor3f(1.0, 0.95, 0.7)
            title_y = int(height * 0.32)
            glRasterPos2f(center_x - 160, title_y)
            for ch in "NOVO RECORDE":
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
            glColor3f(0.95, 0.95, 0.98)
            instr_y = title_y + 36
            glRasterPos2f(center_x - 220, instr_y)
            for ch in "Digite seu nome (Enter para salvar, Esc para pular)":
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
            name_y = instr_y + 42
            glColor3f(1.0, 1.0, 1.0)
            glRasterPos2f(center_x - 120, name_y)
            display = lb_state.name_buffer or "_"
            for ch in display:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
            
            if self.state.game_mode == GAME_MODE_COLLECTOR:
                sline = f"Tempo: {int(self.state.time_alive)}s    Estrelas: {self.state.score}    Dif.: {lb_state.last_played_difficulty or '-'}"
            else:
                sline = f"Pontuação: {self.state.score}    Dif.: {lb_state.last_played_difficulty or '-'}"
            
            glColor3f(0.8, 0.8, 0.85)
            stats_y = name_y + 44
            glRasterPos2f(center_x - 180, stats_y)
            for ch in sline:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        else:
            # Panel background
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(0.1, 0.1, 0.15, 0.75)
            panel_w = 540
            panel_h = 180
            panel_x = center_x - panel_w / 2
            panel_y = int(height * 0.34)
            glBegin(GL_QUADS)
            glVertex2f(panel_x, panel_y)
            glVertex2f(panel_x + panel_w, panel_y)
            glVertex2f(panel_x + panel_w, panel_y + panel_h)
            glVertex2f(panel_x, panel_y + panel_h)
            glEnd()
            glDisable(GL_BLEND)

            glColor3f(1.0, 0.3, 0.3)
            title_y = panel_y + 28
            glRasterPos2f(center_x - 60, title_y)
            for ch in "GAME OVER":
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

            glColor3f(0.9, 0.9, 0.95)
            stats_y = title_y + 36
            glRasterPos2f(center_x - 220, stats_y)
            if self.state.game_mode == GAME_MODE_COLLECTOR:
                stats = f"Tempo: {int(self.state.time_alive)}s    Estrelas: {self.state.score}"
            else:
                stats = f"Pontuação: {self.state.score}    Tempo: {int(self.state.time_alive)}s"
            for ch in stats:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

            glColor3f(0.85, 0.85, 0.9)
            hint_y = stats_y + 44
            glRasterPos2f(center_x - 220, hint_y)
            hints = "Enter: Reiniciar    M: Menu    Q: Sair"
            for ch in hints:
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
