"""Procedural graphics rendering for Blobby Volley: beach, blobs, eyes, ball, and HUD."""

import math
from typing import Tuple
import pygame
from blobby_volley.constants import (
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
    GROUND_Y,
    NET_X,
    NET_WIDTH,
    NET_TOP_Y,
    BLOB_RADIUS,
    BLOB_BODY_HEIGHT,
    BALL_RADIUS,
    COLOR_SKY_TOP,
    COLOR_SKY_BOTTOM,
    COLOR_SEA,
    COLOR_SEA_LIGHT,
    COLOR_SAND,
    COLOR_SAND_DARK,
    COLOR_NET_POST,
    COLOR_NET_MESH,
    COLOR_NET_TOP,
    COLOR_BLOB_LEFT,
    COLOR_BLOB_LEFT_DARK,
    COLOR_BLOB_RIGHT,
    COLOR_BLOB_RIGHT_DARK,
    COLOR_EYE_WHITE,
    COLOR_EYE_PUPIL,
    COLOR_BALL_WHITE,
    COLOR_BALL_STRIPE1,
    COLOR_BALL_STRIPE2,
    COLOR_SHADOW,
    COLOR_TEXT,
    COLOR_HUD_BG,
)
from blobby_volley.physics import Blob, Ball


class GameRenderer:
    """Handles rendering of all game elements onto an internal virtual surface."""

    def __init__(self):
        self.virtual_surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        self.font_large = pygame.font.SysFont("Arial", 40, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 16, bold=False)
        self.anim_time = 0.0

        # Pre-render static background gradient for maximum performance
        self._bg_surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        self._render_background_static()

    def _render_background_static(self) -> None:
        """Create the sky gradient and sea background."""
        # Sky vertical gradient
        for y in range(GROUND_Y):
            ratio = y / float(GROUND_Y)
            r = int(COLOR_SKY_TOP[0] * (1 - ratio) + COLOR_SKY_BOTTOM[0] * ratio)
            g = int(COLOR_SKY_TOP[1] * (1 - ratio) + COLOR_SKY_BOTTOM[1] * ratio)
            b = int(COLOR_SKY_TOP[2] * (1 - ratio) + COLOR_SKY_BOTTOM[2] * ratio)
            pygame.draw.line(self._bg_surface, (r, g, b), (0, y), (VIRTUAL_WIDTH, y))

        # Distant sea band
        sea_top = 370
        pygame.draw.rect(
            self._bg_surface,
            COLOR_SEA,
            (0, sea_top, VIRTUAL_WIDTH, GROUND_Y - sea_top),
        )

        # Distant islands / palm hills for cozy beach feel
        pygame.draw.ellipse(self._bg_surface, (34, 112, 60), (-40, 360, 240, 90))
        pygame.draw.ellipse(self._bg_surface, (39, 130, 70), (620, 350, 260, 100))

        # Soft clouds in the sky
        self._draw_cloud(self._bg_surface, 140, 120, 90)
        self._draw_cloud(self._bg_surface, 560, 90, 120)
        self._draw_cloud(self._bg_surface, 360, 160, 70)

        # Warm beach sand
        pygame.draw.rect(
            self._bg_surface,
            COLOR_SAND,
            (0, GROUND_Y, VIRTUAL_WIDTH, VIRTUAL_HEIGHT - GROUND_Y),
        )
        pygame.draw.line(
            self._bg_surface,
            COLOR_SAND_DARK,
            (0, GROUND_Y),
            (VIRTUAL_WIDTH, GROUND_Y),
            width=3,
        )

    def _draw_cloud(self, surface: pygame.Surface, cx: int, cy: int, width: int) -> None:
        cloud_color = (255, 255, 255, 190)
        c_surf = pygame.Surface((width * 2, 80), pygame.SRCALPHA)
        h = 36
        pygame.draw.ellipse(c_surf, cloud_color, (20, 20, width, h))
        pygame.draw.ellipse(c_surf, cloud_color, (40, 5, int(width * 0.7), h + 10))
        pygame.draw.ellipse(c_surf, cloud_color, (width * 0.4, 15, int(width * 0.6), h))
        surface.blit(c_surf, (cx - width // 2, cy - 40))

    def update(self, dt: float) -> None:
        self.anim_time += dt

    def render(
        self,
        blob_left: Blob,
        blob_right: Blob,
        ball: Ball,
        score_left: int,
        score_right: int,
        server: int,
        match_over: bool = False,
        winner: int = 0,
        paused: bool = False,
    ) -> pygame.Surface:
        """Render complete game scene onto virtual surface."""
        # 1. Blit static background
        self.virtual_surface.blit(self._bg_surface, (0, 0))

        # 2. Animated waves on the water
        wave_offset = math.sin(self.anim_time * 2.5) * 4.0
        pygame.draw.line(
            self.virtual_surface,
            COLOR_SEA_LIGHT,
            (0, int(372 + wave_offset)),
            (VIRTUAL_WIDTH, int(372 - wave_offset)),
            width=2,
        )

        # 3. Shadows on the sand
        self._render_shadows(blob_left, blob_right, ball)

        # 4. Volleyball net
        self._render_net()

        # 5. Blobs
        self._render_blob(blob_left, is_left=True, ball=ball)
        self._render_blob(blob_right, is_left=False, ball=ball)

        # 6. Volleyball
        self._render_ball(ball)

        # 7. HUD & Scoreboard
        self._render_hud(score_left, score_right, server, blob_left, blob_right)

        # 8. Overlays (Pause / Match Over)
        if paused:
            self._render_overlay("PAUSE", "Drücke ESC zum Weiterspielen")
        elif match_over:
            win_text = "SPIELER 1 GEWINNT!" if winner == 1 else "SPIELER 2 GEWINNT!"
            self._render_overlay(win_text, "Drücke R für ein neues Spiel oder ESC für das Menü")

        return self.virtual_surface

    def _render_shadows(self, blob_left: Blob, blob_right: Blob, ball: Ball) -> None:
        shadow_surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)

        # Left blob shadow
        scale_l = max(0.6, 1.0 - (GROUND_Y - blob_left.y) / 400.0)
        sw_l = int(BLOB_RADIUS * 2.2 * scale_l)
        sh_l = int(14 * scale_l)
        pygame.draw.ellipse(
            shadow_surf,
            COLOR_SHADOW,
            (int(blob_left.x - sw_l / 2), int(GROUND_Y - sh_l / 2), sw_l, sh_l),
        )

        # Right blob shadow
        scale_r = max(0.6, 1.0 - (GROUND_Y - blob_right.y) / 400.0)
        sw_r = int(BLOB_RADIUS * 2.2 * scale_r)
        sh_r = int(14 * scale_r)
        pygame.draw.ellipse(
            shadow_surf,
            COLOR_SHADOW,
            (int(blob_right.x - sw_r / 2), int(GROUND_Y - sh_r / 2), sw_r, sh_r),
        )

        # Ball shadow
        height_above_ground = max(0.0, GROUND_Y - (ball.y + BALL_RADIUS))
        ball_scale = max(0.4, 1.0 - height_above_ground / 600.0)
        ball_sw = int(BALL_RADIUS * 2.0 * ball_scale)
        ball_sh = int(10 * ball_scale)
        alpha = int(max(20, 110 * ball_scale))
        pygame.draw.ellipse(
            shadow_surf,
            (0, 0, 0, alpha),
            (int(ball.x - ball_sw / 2), int(GROUND_Y - ball_sh / 2), ball_sw, ball_sh),
        )

        self.virtual_surface.blit(shadow_surf, (0, 0))

    def _render_net(self) -> None:
        post_x = int(NET_X - NET_WIDTH / 2)
        # Net post
        pygame.draw.rect(
            self.virtual_surface,
            COLOR_NET_POST,
            (post_x, NET_TOP_Y, NET_WIDTH, GROUND_Y - NET_TOP_Y),
        )
        # Top rounded red band
        pygame.draw.circle(
            self.virtual_surface,
            COLOR_NET_TOP,
            (int(NET_X), NET_TOP_Y),
            int(NET_WIDTH / 2 + 1),
        )
        # Net grid lines
        for y in range(NET_TOP_Y + 14, GROUND_Y, 16):
            pygame.draw.line(
                self.virtual_surface,
                COLOR_NET_MESH,
                (post_x, y),
                (post_x + NET_WIDTH, y),
                width=1,
            )
        pygame.draw.line(
            self.virtual_surface,
            COLOR_NET_MESH,
            (NET_X, NET_TOP_Y),
            (NET_X, GROUND_Y),
            width=1,
        )

    def _render_blob(self, blob: Blob, is_left: bool, ball: Ball) -> None:
        """Render a cute Blobby with procedural body, outline, two ball-tracking eyes and smile."""
        color = COLOR_BLOB_LEFT if is_left else COLOR_BLOB_RIGHT
        color_dark = COLOR_BLOB_LEFT_DARK if is_left else COLOR_BLOB_RIGHT_DARK

        bx = int(blob.x)
        by = int(blob.y)

        # Dome center
        dome_y = by - BLOB_BODY_HEIGHT
        r = BLOB_RADIUS

        # Blob body outline (composite rounded shape)
        body_rect = pygame.Rect(bx - r, dome_y, r * 2, BLOB_BODY_HEIGHT)

        # Draw darker outline first for clean separation
        pygame.draw.circle(self.virtual_surface, color_dark, (bx, dome_y), r + 2)
        pygame.draw.rect(
            self.virtual_surface,
            color_dark,
            (bx - r - 2, dome_y, (r + 2) * 2, BLOB_BODY_HEIGHT),
            border_bottom_left_radius=14,
            border_bottom_right_radius=14,
        )

        # Draw inner filled blob
        pygame.draw.circle(self.virtual_surface, color, (bx, dome_y), r)
        pygame.draw.rect(
            self.virtual_surface,
            color,
            body_rect,
            border_bottom_left_radius=12,
            border_bottom_right_radius=12,
        )

        # Two ball-tracking eyes
        # Eye positions relative to center dome: back eye and front eye
        eye_sign = 1 if is_left else -1
        eye_back_center = (bx - eye_sign * 5, dome_y - 2)
        eye_front_center = (bx + eye_sign * 15, dome_y - 2)
        eye_back_radius = int(r * 0.28)
        eye_front_radius = int(r * 0.33)

        # Draw both eyes
        for ec_x, ec_y, er in [
            (eye_back_center[0], eye_back_center[1], eye_back_radius),
            (eye_front_center[0], eye_front_center[1], eye_front_radius),
        ]:
            # White eyeball
            pygame.draw.circle(self.virtual_surface, COLOR_EYE_WHITE, (ec_x, ec_y), er)
            pygame.draw.circle(self.virtual_surface, (50, 50, 50), (ec_x, ec_y), er, width=1)

            # Pupil direction vector towards ball
            p_dx = ball.x - ec_x
            p_dy = ball.y - ec_y
            p_dist = math.hypot(p_dx, p_dy)
            pupil_max_shift = er * 0.45
            if p_dist > 0.1:
                p_shift_x = (p_dx / p_dist) * pupil_max_shift
                p_shift_y = (p_dy / p_dist) * pupil_max_shift
            else:
                p_shift_x, p_shift_y = 0.0, 0.0

            pupil_x = int(ec_x + p_shift_x)
            pupil_y = int(ec_y + p_shift_y)
            pupil_r = max(2, int(er * 0.46))
            pygame.draw.circle(self.virtual_surface, COLOR_EYE_PUPIL, (pupil_x, pupil_y), pupil_r)
            # Tiny white shine in pupil
            pygame.draw.circle(self.virtual_surface, (255, 255, 255), (pupil_x - 1, pupil_y - 1), 1)

        # Subtle cheerful smile
        mouth_x = bx + (eye_sign * 6)
        mouth_y = dome_y + 16
        mouth_rect = pygame.Rect(mouth_x - 7, mouth_y - 3, 14, 8)
        pygame.draw.arc(self.virtual_surface, color_dark, mouth_rect, math.pi * 1.1, math.pi * 1.9, 2)

    def _render_ball(self, ball: Ball) -> None:
        """Render rotating striped volleyball."""
        bx = int(ball.x)
        by = int(ball.y)
        r = BALL_RADIUS

        # Ball shadow base outline
        pygame.draw.circle(self.virtual_surface, (30, 30, 30), (bx, by), r + 1)
        pygame.draw.circle(self.virtual_surface, COLOR_BALL_WHITE, (bx, by), r)

        # Draw rotating colored curved stripes
        rot = ball.rotation
        for i, color in enumerate([COLOR_BALL_STRIPE1, COLOR_BALL_STRIPE2]):
            angle = rot + (i * math.pi)
            p1_x = bx + int(math.cos(angle) * r)
            p1_y = by + int(math.sin(angle) * r)
            p2_x = bx + int(math.cos(angle + math.pi * 0.6) * r)
            p2_y = by + int(math.sin(angle + math.pi * 0.6) * r)
            pygame.draw.line(self.virtual_surface, color, (p1_x, p1_y), (p2_x, p2_y), width=4)

        # Subtle 3D ball highlight
        pygame.draw.circle(self.virtual_surface, (255, 255, 255, 100), (bx - 5, by - 5), int(r * 0.35))

    def _render_hud(
        self,
        score_left: int,
        score_right: int,
        server: int,
        blob_left: Blob,
        blob_right: Blob,
    ) -> None:
        """Render retro score display with serve and touches indicators."""
        # Top HUD banner
        hud_w, hud_h = 280, 68
        hud_x = (VIRTUAL_WIDTH - hud_w) // 2
        hud_y = 12

        hud_surf = pygame.Surface((hud_w, hud_h), pygame.SRCALPHA)
        pygame.draw.rect(hud_surf, COLOR_HUD_BG, (0, 0, 0 + hud_w, hud_h), border_radius=12)
        pygame.draw.rect(hud_surf, (255, 255, 255, 40), (0, 0, hud_w, hud_h), width=1, border_radius=12)
        self.virtual_surface.blit(hud_surf, (hud_x, hud_y))

        # Scores
        score_left_text = self.font_large.render(f"{score_left:02d}", True, COLOR_BLOB_LEFT)
        score_right_text = self.font_large.render(f"{score_right:02d}", True, COLOR_BLOB_RIGHT)
        colon_text = self.font_large.render(":", True, COLOR_TEXT)

        cx = VIRTUAL_WIDTH // 2
        self.virtual_surface.blit(colon_text, colon_text.get_rect(center=(cx, hud_y + 32)))
        self.virtual_surface.blit(score_left_text, score_left_text.get_rect(center=(cx - 60, hud_y + 32)))
        self.virtual_surface.blit(score_right_text, score_right_text.get_rect(center=(cx + 60, hud_y + 32)))

        # Serve indicator dots
        dot_left_color = (255, 215, 0) if server == 1 else (80, 80, 80)
        dot_right_color = (255, 215, 0) if server == 2 else (80, 80, 80)
        pygame.draw.circle(self.virtual_surface, dot_left_color, (cx - 105, hud_y + 32), 6)
        pygame.draw.circle(self.virtual_surface, dot_right_color, (cx + 105, hud_y + 32), 6)

        # Touches display below HUD (1/3, 2/3 dots)
        for i in range(3):
            # Left touches
            active_l = i < blob_left.touches
            color_l = COLOR_BLOB_LEFT if active_l else (70, 70, 70)
            pygame.draw.circle(self.virtual_surface, color_l, (cx - 75 + i * 14, hud_y + 56), 4)

            # Right touches
            active_r = i < blob_right.touches
            color_r = COLOR_BLOB_RIGHT if active_r else (70, 70, 70)
            pygame.draw.circle(self.virtual_surface, color_r, (cx + 47 + i * 14, hud_y + 56), 4)

    def _render_overlay(self, title: str, subtitle: str) -> None:
        """Render translucent dark overlay for Pause or Game Over."""
        overlay = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.virtual_surface.blit(overlay, (0, 0))

        title_surf = self.font_large.render(title, True, (255, 255, 255))
        sub_surf = self.font_medium.render(subtitle, True, (240, 240, 240))

        cx = VIRTUAL_WIDTH // 2
        cy = VIRTUAL_HEIGHT // 2
        self.virtual_surface.blit(title_surf, title_surf.get_rect(center=(cx, cy - 30)))
        self.virtual_surface.blit(sub_surf, sub_surf.get_rect(center=(cx, cy + 25)))
