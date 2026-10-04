"""Main application entry point with menu, fullscreen toggle, and game loop."""

import sys
import pygame
from blobby_volley.constants import (
    VIRTUAL_WIDTH,
    VIRTUAL_HEIGHT,
    TARGET_FPS,
    AI_DIFFICULTIES,
    COLOR_SKY_TOP,
    COLOR_SKY_BOTTOM,
    COLOR_BLOB_LEFT,
    COLOR_BLOB_RIGHT,
    COLOR_TEXT,
)
from blobby_volley.audio import SoundManager
from blobby_volley.render import GameRenderer
from blobby_volley.game import GameState


class WindowManager:
    """Manages windowed and fullscreen display states with aspect-ratio preservation."""

    def __init__(self, title: str = "Blobby Volley"):
        self.title = title
        self.is_fullscreen = False
        self.window_width = VIRTUAL_WIDTH
        self.window_height = VIRTUAL_HEIGHT

        pygame.display.set_caption(self.title)
        self.screen = pygame.display.set_mode(
            (self.window_width, self.window_height),
            pygame.RESIZABLE,
        )

    def toggle_fullscreen(self) -> None:
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            # Switch to desktop resolution fullscreen
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            # Switch back to windowed mode
            self.screen = pygame.display.set_mode(
                (self.window_width, self.window_height),
                pygame.RESIZABLE,
            )

    def present(self, virtual_surface: pygame.Surface) -> None:
        """Scales virtual surface onto screen preserving aspect ratio."""
        scr_w, scr_h = self.screen.get_size()
        scale = min(scr_w / float(VIRTUAL_WIDTH), scr_h / float(VIRTUAL_HEIGHT))
        dest_w = int(VIRTUAL_WIDTH * scale)
        dest_h = int(VIRTUAL_HEIGHT * scale)
        dest_x = (scr_w - dest_w) // 2
        dest_y = (scr_h - dest_h) // 2

        self.screen.fill((10, 15, 20))  # Letterbox border color
        scaled = pygame.transform.smoothscale(virtual_surface, (dest_w, dest_h))
        self.screen.blit(scaled, (dest_x, dest_y))
        pygame.display.flip()

    def screen_to_virtual(self, sx: int, sy: int) -> tuple[float, float]:
        """Convert actual screen coordinates to virtual coordinates."""
        scr_w, scr_h = self.screen.get_size()
        scale = min(scr_w / float(VIRTUAL_WIDTH), scr_h / float(VIRTUAL_HEIGHT))
        dest_w = int(VIRTUAL_WIDTH * scale)
        dest_h = int(VIRTUAL_HEIGHT * scale)
        dest_x = (scr_w - dest_w) // 2
        dest_y = (scr_h - dest_h) // 2
        vx = (sx - dest_x) / scale
        vy = (sy - dest_y) / scale
        return (vx, vy)


class MenuScreen:
    """Retro style main menu for mode selection, difficulty, and controls."""

    def __init__(self):
        self.font_title = pygame.font.SysFont("Arial", 56, bold=True)
        self.font_btn = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_info = pygame.font.SysFont("Arial", 18, bold=False)

        self.difficulty_list = list(AI_DIFFICULTIES.keys())
        self.current_diff_idx = 1  # "Mittel" default
        self.selected_index = 0

        self.items = [
            "1 Spieler (vs. Computer)",
            "2 Spieler (Lokal)",
            "Schwierigkeit: Mittel",
            "Steuerung anzeigen",
            "Beenden",
        ]
        self.show_controls = False

    def update_diff_text(self) -> None:
        diff = self.difficulty_list[self.current_diff_idx]
        self.items[2] = f"Schwierigkeit: {diff}"

    def cycle_difficulty(self) -> str:
        self.current_diff_idx = (self.current_diff_idx + 1) % len(self.difficulty_list)
        self.update_diff_text()
        return self.difficulty_list[self.current_diff_idx]

    def render(self, surface: pygame.Surface) -> None:
        """Render stylish beach menu with buttons."""
        # Sky gradient
        for y in range(VIRTUAL_HEIGHT):
            ratio = y / float(VIRTUAL_HEIGHT)
            r = int(COLOR_SKY_TOP[0] * (1 - ratio) + COLOR_SKY_BOTTOM[0] * ratio)
            g = int(COLOR_SKY_TOP[1] * (1 - ratio) + COLOR_SKY_BOTTOM[1] * ratio)
            b = int(COLOR_SKY_TOP[2] * (1 - ratio) + COLOR_SKY_BOTTOM[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (VIRTUAL_WIDTH, y))

        # Title with shadow
        title_str = "BLOBBY VOLLEY"
        cx = VIRTUAL_WIDTH // 2
        title_shadow = self.font_title.render(title_str, True, (20, 40, 60))
        title_text = self.font_title.render(title_str, True, (255, 230, 0))
        surface.blit(title_shadow, title_shadow.get_rect(center=(cx + 3, 113)))
        surface.blit(title_text, title_text.get_rect(center=(cx, 110)))

        # Subtitle
        sub_text = self.font_info.render("Klassische Python-Adaption mit Pygame", True, (240, 245, 255))
        surface.blit(sub_text, sub_text.get_rect(center=(cx, 160)))

        # Menu Buttons
        btn_w, btn_h = 420, 48
        start_y = 210

        if not self.show_controls:
            for idx, item in enumerate(self.items):
                by = start_y + idx * (btn_h + 14)
                rect = pygame.Rect(cx - btn_w // 2, by, btn_w, btn_h)

                is_selected = idx == self.selected_index
                bg_color = (40, 60, 90, 230) if not is_selected else (241, 196, 15, 240)
                border_color = (255, 255, 255, 180) if not is_selected else (255, 255, 255, 255)
                text_color = COLOR_TEXT if not is_selected else (20, 20, 20)

                btn_surf = pygame.Surface((btn_w, btn_h), pygame.SRCALPHA)
                pygame.draw.rect(btn_surf, bg_color, (0, 0, btn_w, btn_h), border_radius=10)
                pygame.draw.rect(btn_surf, border_color, (0, 0, btn_w, btn_h), width=2, border_radius=10)
                surface.blit(btn_surf, (rect.x, rect.y))

                label = self.font_btn.render(item, True, text_color)
                surface.blit(label, label.get_rect(center=rect.center))
        else:
            self._render_controls_panel(surface, cx, start_y)

        # Footer hints
        footer_str = "Navigation: Pfeiltasten | Bestätigen: ENTER | Vollbild: F11"
        footer_text = self.font_info.render(footer_str, True, (220, 230, 240))
        surface.blit(footer_text, footer_text.get_rect(center=(cx, VIRTUAL_HEIGHT - 30)))

    def _render_controls_panel(self, surface: pygame.Surface, cx: int, y: int) -> None:
        panel_w, panel_h = 580, 290
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (20, 35, 55, 240), (0, 0, panel_w, panel_h), border_radius=12)
        pygame.draw.rect(panel_surf, (255, 255, 255, 180), (0, 0, panel_w, panel_h), width=2, border_radius=12)
        surface.blit(panel_surf, (cx - panel_w // 2, y))

        lines = [
            ("STEUERUNG", (255, 215, 0), self.font_btn),
            ("Spieler 1 (Grün):  A = Links,  D = Rechts,  W = Springen", COLOR_BLOB_LEFT, self.font_info),
            ("Spieler 2 (Rot):   Links,  Rechts,  Hoch = Springen", COLOR_BLOB_RIGHT, self.font_info),
            ("Allgemein:", (255, 255, 255), self.font_info),
            ("F11 = Vollbild an/aus  |  ESC = Pause / Menü  |  R = Neustart", (200, 220, 240), self.font_info),
            ("Drücke ENTER oder ESC zum Zurückkehren", (241, 196, 15), self.font_info),
        ]

        cy = y + 25
        for text, col, font in lines:
            rendered = font.render(text, True, col)
            surface.blit(rendered, rendered.get_rect(center=(cx, cy)))
            cy += 40


def main() -> None:
    """Application main loop."""
    pygame.init()
    clock = pygame.time.Clock()

    window = WindowManager(title="Blobby Volley")
    audio = SoundManager()
    renderer = GameRenderer()
    menu = MenuScreen()

    game: GameState | None = None
    app_state = "MENU"  # "MENU" or "PLAYING"

    running = True
    while running:
        dt = clock.tick(TARGET_FPS) / 1000.0
        # Cap dt to prevent physics jumps if window is moved
        dt = min(dt, 0.05)

        # 1. Event processing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    window.toggle_fullscreen()

                elif app_state == "MENU":
                    if menu.show_controls:
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                            menu.show_controls = False
                    else:
                        if event.key in (pygame.K_UP, pygame.K_w):
                            menu.selected_index = (menu.selected_index - 1) % len(menu.items)
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            menu.selected_index = (menu.selected_index + 1) % len(menu.items)
                        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            idx = menu.selected_index
                            if idx == 0:  # 1 Player vs Bot
                                diff = menu.difficulty_list[menu.current_diff_idx]
                                game = GameState(mode="vs_bot", difficulty=diff, sound_manager=audio)
                                app_state = "PLAYING"
                            elif idx == 1:  # 2 Player Local
                                game = GameState(mode="2p_local", sound_manager=audio)
                                app_state = "PLAYING"
                            elif idx == 2:  # Difficulty toggle
                                menu.cycle_difficulty()
                            elif idx == 3:  # Show controls
                                menu.show_controls = True
                            elif idx == 4:  # Exit
                                running = False

                elif app_state == "PLAYING" and game is not None:
                    if event.key == pygame.K_ESCAPE:
                        if game.match_over:
                            app_state = "MENU"
                        else:
                            game.toggle_pause()
                    elif event.key == pygame.K_r:
                        game.restart_match()

            elif event.type == pygame.MOUSEMOTION and app_state == "MENU" and not menu.show_controls:
                vx, vy = window.screen_to_virtual(*event.pos)
                cx = VIRTUAL_WIDTH // 2
                btn_w, btn_h = 420, 48
                start_y = 210
                for idx in range(len(menu.items)):
                    by = start_y + idx * (btn_h + 14)
                    if (cx - btn_w // 2 <= vx <= cx + btn_w // 2) and (by <= vy <= by + btn_h):
                        menu.selected_index = idx
                        break

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and app_state == "MENU":
                if menu.show_controls:
                    menu.show_controls = False
                else:
                    vx, vy = window.screen_to_virtual(*event.pos)
                    cx = VIRTUAL_WIDTH // 2
                    btn_w, btn_h = 420, 48
                    start_y = 210
                    for idx in range(len(menu.items)):
                        by = start_y + idx * (btn_h + 14)
                        if (cx - btn_w // 2 <= vx <= cx + btn_w // 2) and (by <= vy <= by + btn_h):
                            menu.selected_index = idx
                            if idx == 0:
                                diff = menu.difficulty_list[menu.current_diff_idx]
                                game = GameState(mode="vs_bot", difficulty=diff, sound_manager=audio)
                                app_state = "PLAYING"
                            elif idx == 1:
                                game = GameState(mode="2p_local", sound_manager=audio)
                                app_state = "PLAYING"
                            elif idx == 2:
                                menu.cycle_difficulty()
                            elif idx == 3:
                                menu.show_controls = True
                            elif idx == 4:
                                running = False
                            break

        if not running:
            break

        # 2. Logic & Rendering
        if app_state == "MENU":
            menu_surface = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
            menu.render(menu_surface)
            window.present(menu_surface)

        elif app_state == "PLAYING" and game is not None:
            # Poll keys for player movement
            keys = pygame.key.get_pressed()

            # Player 1 controls (W/A/D)
            p1_dir = 0.0
            if keys[pygame.K_a]:
                p1_dir -= 1.0
            if keys[pygame.K_d]:
                p1_dir += 1.0
            p1_jump = bool(keys[pygame.K_w])

            # Player 2 controls (Arrow keys)
            p2_dir = 0.0
            if keys[pygame.K_LEFT]:
                p2_dir -= 1.0
            if keys[pygame.K_RIGHT]:
                p2_dir += 1.0
            p2_jump = bool(keys[pygame.K_UP])

            game.update(dt, p1_dir, p1_jump, p2_dir, p2_jump)
            renderer.update(dt)

            frame = renderer.render(
                blob_left=game.blob_left,
                blob_right=game.blob_right,
                ball=game.ball,
                score_left=game.score_left,
                score_right=game.score_right,
                server=game.server,
                match_over=game.match_over,
                winner=game.winner,
                paused=game.paused,
            )
            window.present(frame)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
