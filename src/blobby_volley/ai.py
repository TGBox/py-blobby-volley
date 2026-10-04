"""Bot AI controller with physics prediction and configurable difficulty."""

import math
import random
from typing import Tuple
from blobby_volley.constants import (
    VIRTUAL_WIDTH,
    GROUND_Y,
    NET_X,
    NET_WIDTH,
    BLOB_RADIUS,
    BLOB_BODY_HEIGHT,
    BALL_RADIUS,
    BALL_GRAVITY,
    AI_DIFFICULTIES,
)
from blobby_volley.physics import Blob, Ball


class BotAI:
    """Controls player 2 (right blob) with predictive arcade volleyball AI."""

    def __init__(self, difficulty: str = "Mittel"):
        self.difficulty = difficulty
        self.config = AI_DIFFICULTIES.get(difficulty, AI_DIFFICULTIES["Mittel"])
        self.home_x = 620.0
        self.target_x = self.home_x
        self.reaction_timer = 0.0
        self.jitter_offset = 0.0

    def set_difficulty(self, difficulty: str) -> None:
        self.difficulty = difficulty
        self.config = AI_DIFFICULTIES.get(difficulty, AI_DIFFICULTIES["Mittel"])

    def update(self, dt: float, bot_blob: Blob, ball: Ball) -> Tuple[float, bool]:
        """
        Calculates move direction (-1.0 to 1.0) and jump decision.
        Returns:
            (move_dir, jump_pressed)
        """
        self.reaction_timer -= dt

        # Update decision only when reaction timer lapses
        if self.reaction_timer <= 0.0:
            self.reaction_timer = self.config["reaction_delay"]
            jitter_range = self.config["jitter"]
            self.jitter_offset = random.uniform(-jitter_range, jitter_range)
            self.target_x = self._calculate_target_x(bot_blob, ball)

        # Movement towards target position
        dx = self.target_x - bot_blob.x
        deadzone = 6.0
        if dx < -deadzone:
            move_dir = -1.0
        elif dx > deadzone:
            move_dir = 1.0
        else:
            move_dir = 0.0

        # Jump decision logic
        jump_pressed = False
        ball_on_my_side = ball.x > NET_X - 20
        dist_to_ball_x = abs(bot_blob.x - ball.x)

        if ball_on_my_side and bot_blob.is_grounded:
            # Check if ball is dropping in our zone and in hit range
            is_above_head = (
                ball.y < bot_blob.y - BLOB_BODY_HEIGHT + 20
                and ball.y > bot_blob.y - BLOB_BODY_HEIGHT - 120
            )
            if dist_to_ball_x < (BLOB_RADIUS + BALL_RADIUS + 10) and is_above_head:
                if random.random() < self.config["jump_chance"]:
                    jump_pressed = True

        return (move_dir, jump_pressed)

    def _calculate_target_x(self, bot_blob: Blob, ball: Ball) -> float:
        """Predict ball trajectory to choose defense or attack intercept position."""
        # If ball is far on opponent's court, return to base defense
        if ball.x < NET_X:
            return self.home_x + self.jitter_offset

        # Solve for time when ball reaches blob head height
        target_y = float(GROUND_Y - BLOB_BODY_HEIGHT)
        g = BALL_GRAVITY
        dy = ball.y - target_y
        vy = ball.vy

        # Quadratic equation: 0.5 * g * t^2 + vy * t + dy = 0
        discriminant = vy * vy - 2.0 * g * dy
        if discriminant >= 0:
            t = (-vy + math.sqrt(discriminant)) / g
            if t <= 0:
                t = 0.2
        else:
            t = 0.25

        # Predicted horizontal landing / hit coordinate
        pred_x = ball.x + ball.vx * t

        # Handle simple wall bounce on right wall
        right_wall = VIRTUAL_WIDTH - BALL_RADIUS
        if pred_x > right_wall:
            excess = pred_x - right_wall
            pred_x = right_wall - excess

        # Offset slightly behind the ball (to the right) so the hit directs ball left
        hit_bias = 14.0
        desired_x = pred_x + hit_bias + self.jitter_offset

        # Clamp target inside right half of the court
        min_bound = NET_X + (NET_WIDTH / 2.0) + BLOB_RADIUS + 5
        max_bound = VIRTUAL_WIDTH - BLOB_RADIUS - 5
        return max(min_bound, min(desired_x, max_bound))
