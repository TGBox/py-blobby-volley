"""Game state, scoring rules, match flow and serve management."""

from typing import Optional
from blobby_volley.constants import (
    POINTS_TO_WIN,
    MAX_TOUCHES,
    SERVE_LEFT_X,
    SERVE_RIGHT_X,
    SERVE_BALL_Y,
    NET_X,
)
from blobby_volley.physics import Blob, Ball, PhysicsWorld
from blobby_volley.audio import SoundManager
from blobby_volley.ai import BotAI


class GameState:
    """Manages full match state, scoring rules, serve cycles, and player entities."""

    def __init__(
        self,
        mode: str = "vs_bot",
        difficulty: str = "Mittel",
        sound_manager: Optional[SoundManager] = None,
    ):
        self.mode = mode
        self.blob_left = Blob(x=SERVE_LEFT_X, is_left=True)
        self.blob_right = Blob(x=SERVE_RIGHT_X, is_left=False)
        self.ball = Ball(x=SERVE_LEFT_X, y=SERVE_BALL_Y)
        self.physics = PhysicsWorld(self.blob_left, self.blob_right, self.ball)
        self.audio = sound_manager or SoundManager()
        self.ai = BotAI(difficulty=difficulty)

        self.score_left = 0
        self.score_right = 0
        self.server = 1  # 1 for left, 2 for right
        self.match_over = False
        self.winner = 0
        self.paused = False

        self.serve_delay = 0.6  # Seconds before ball begins falling
        self.serve_timer = self.serve_delay
        self.rally_in_progress = False

        self._reset_positions_for_serve()

    def set_difficulty(self, diff: str) -> None:
        self.ai.set_difficulty(diff)

    def restart_match(self) -> None:
        """Reset scores and start fresh match."""
        self.score_left = 0
        self.score_right = 0
        self.server = 1
        self.match_over = False
        self.winner = 0
        self.paused = False
        self._reset_positions_for_serve()

    def toggle_pause(self) -> None:
        if not self.match_over:
            self.paused = not self.paused

    def _reset_positions_for_serve(self) -> None:
        """Place players and ball in serve positions."""
        self.blob_left.reset_position(SERVE_LEFT_X)
        self.blob_right.reset_position(SERVE_RIGHT_X)

        serve_x = SERVE_LEFT_X if self.server == 1 else SERVE_RIGHT_X
        self.ball.reset(serve_x, SERVE_BALL_Y, vx=0.0, vy=0.0)

        self.serve_timer = self.serve_delay
        self.rally_in_progress = False

    def update(
        self,
        dt: float,
        p1_dir: float,
        p1_jump: bool,
        p2_dir: float = 0.0,
        p2_jump: bool = False,
    ) -> None:
        """
        Step game logic by dt seconds.
        Handles player inputs, AI decision, physics updates, and referee scoring.
        """
        if self.paused or self.match_over:
            return

        # Handle serve countdown
        if self.serve_timer > 0.0:
            self.serve_timer -= dt
            # Keep ball hovering at serve height until timer expires
            serve_x = SERVE_LEFT_X if self.server == 1 else SERVE_RIGHT_X
            self.ball.reset(serve_x, SERVE_BALL_Y, vx=0.0, vy=0.0)

            # Players can still adjust horizontal position
            self.blob_left.update(dt, p1_dir, p1_jump)
            if self.mode == "vs_bot":
                self.blob_right.update(dt, 0.0, False)
            else:
                self.blob_right.update(dt, p2_dir, p2_jump)

            if self.serve_timer <= 0.0:
                self.rally_in_progress = True
                self.audio.play("whistle")
            return

        # 1. Update player 1
        self.blob_left.update(dt, p1_dir, p1_jump)

        # 2. Update player 2 (Human or Bot)
        if self.mode == "vs_bot":
            ai_dir, ai_jump = self.ai.update(dt, self.blob_right, self.ball)
            self.blob_right.update(dt, ai_dir, ai_jump)
        else:
            self.blob_right.update(dt, p2_dir, p2_jump)

        # 3. Update physics
        hit_occurred, hit_sound, ground_side = self.physics.update(dt)

        if hit_occurred and hit_sound:
            self.audio.play(hit_sound)

        # Reset touch count when ball crosses the net
        if self.ball.x < NET_X and self.blob_right.touches > 0:
            self.blob_right.touches = 0
        elif self.ball.x > NET_X and self.blob_left.touches > 0:
            self.blob_left.touches = 0

        # Check touch fault (> 3 touches on one side)
        fault_loser: Optional[int] = None
        if self.blob_left.touches > MAX_TOUCHES:
            fault_loser = 1
        elif self.blob_right.touches > MAX_TOUCHES:
            fault_loser = 2

        # 4. Check rally conclusion (Ground hit or fault)
        if ground_side is not None or fault_loser is not None:
            rally_loser = ground_side if ground_side is not None else fault_loser
            self._handle_rally_end(loser=rally_loser)

    def _handle_rally_end(self, loser: Optional[int]) -> None:
        """Score calculation according to classic volleyball side-out rules."""
        if loser is None:
            return

        winner = 2 if loser == 1 else 1

        if winner == self.server:
            # Server wins rally -> Award point
            if winner == 1:
                self.score_left += 1
            else:
                self.score_right += 1
            self.audio.play("score")
        else:
            # Receiver wins rally -> Side-out (wins serve, but no point awarded)
            self.server = winner
            self.audio.play("whistle")

        # Check for match victory (first to 15, lead by at least 2)
        score_diff = abs(self.score_left - self.score_right)
        if (self.score_left >= POINTS_TO_WIN or self.score_right >= POINTS_TO_WIN) and score_diff >= 2:
            self.match_over = True
            self.winner = 1 if self.score_left > self.score_right else 2
        else:
            self._reset_positions_for_serve()
