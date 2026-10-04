"""Physics simulation, collision detection, and vector math for Blobby Volley."""

import math
from typing import Optional, Tuple
from blobby_volley.constants import (
    VIRTUAL_WIDTH,
    GROUND_Y,
    NET_X,
    NET_WIDTH,
    NET_TOP_Y,
    BLOB_RADIUS,
    BLOB_BODY_HEIGHT,
    BLOB_SPEED,
    BLOB_JUMP_SPEED,
    BLOB_GRAVITY,
    BALL_RADIUS,
    BALL_GRAVITY,
    BALL_MAX_SPEED,
    BALL_MIN_BOUNCE,
    BALL_RESTITUTION_WALL,
    BALL_RESTITUTION_NET,
    JELLY_PROFILES,
)


class Blob:
    """Represents a player blob with kinematic movement, jump physics and spring-damper jelly deformation."""

    def __init__(self, x: float, is_left: bool, jelly_mode: str = "Normal"):
        self.x: float = x
        self.y: float = float(GROUND_Y)  # Bottom of the blob on the ground
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.is_left: bool = is_left
        self.is_grounded: bool = True
        self.touches: int = 0
        self.jelly_mode: str = jelly_mode

        # Spring-damper oscillator states (purely visual deformation)
        self.squish_y: float = 0.0
        self.squish_vy: float = 0.0
        self.impact_x: float = 0.0
        self.impact_y: float = 0.0
        self.impact_vx: float = 0.0
        self.impact_vy: float = 0.0
        self.tilt: float = 0.0

        # Min and max horizontal bounds
        if is_left:
            self.min_x = float(BLOB_RADIUS)
            self.max_x = float(NET_X - (NET_WIDTH / 2) - BLOB_RADIUS)
        else:
            self.min_x = float(NET_X + (NET_WIDTH / 2) + BLOB_RADIUS)
            self.max_x = float(VIRTUAL_WIDTH - BLOB_RADIUS)

    @property
    def head_center(self) -> Tuple[float, float]:
        """Center of the top spherical dome."""
        return (self.x, self.y - BLOB_BODY_HEIGHT)

    @property
    def scale_y(self) -> float:
        """Vertical deformation scale factor with clamping."""
        profile = JELLY_PROFILES.get(self.jelly_mode, JELLY_PROFILES["Normal"])
        max_d = profile["max_deformation"]
        val = max(-max_d, min(max_d, self.squish_y))
        return max(0.25, 1.0 + val)

    @property
    def scale_x(self) -> float:
        """Horizontal deformation scale preserving volume (Sx * Sy ~= 1)."""
        return 1.0 / math.sqrt(self.scale_y)

    def set_jelly_mode(self, mode: str) -> None:
        self.jelly_mode = mode

    def reset_position(self, x: float) -> None:
        self.x = x
        self.y = float(GROUND_Y)
        self.vx = 0.0
        self.vy = 0.0
        self.is_grounded = True
        self.touches = 0
        self.squish_y = 0.0
        self.squish_vy = 0.0
        self.impact_x = 0.0
        self.impact_y = 0.0
        self.impact_vx = 0.0
        self.impact_vy = 0.0
        self.tilt = 0.0

    def apply_impact(self, nx: float, ny: float, impact_speed: float) -> None:
        """Apply directional elastic impulse when the ball strikes the blob."""
        profile = JELLY_PROFILES.get(self.jelly_mode, JELLY_PROFILES["Normal"])
        norm_speed = min(3.0, max(0.5, impact_speed / 240.0))
        strength = profile["impact_strength"] * norm_speed

        # Push inward in direction opposite to contact normal
        self.impact_vx -= nx * strength * 180.0
        self.impact_vy -= ny * strength * 180.0

        # Vertical squish excitation
        self.squish_vy += ny * strength * 15.0

    def update(self, dt: float, move_dir: float, jump_pressed: bool) -> None:
        """Update blob position, velocity, and spring-damper deformation."""
        profile = JELLY_PROFILES.get(self.jelly_mode, JELLY_PROFILES["Normal"])

        # Horizontal movement
        self.vx = move_dir * BLOB_SPEED
        self.x += self.vx * dt

        # Clamp horizontal position to court half
        if self.x < self.min_x:
            self.x = self.min_x
        elif self.x > self.max_x:
            self.x = self.max_x

        # Jump initiation (triggers vertical stretch)
        if jump_pressed and self.is_grounded:
            self.vy = BLOB_JUMP_SPEED
            self.is_grounded = False
            self.squish_vy += profile["jump_stretch"] * 24.0

        # Vertical gravity and integration
        if not self.is_grounded:
            self.vy += BLOB_GRAVITY * dt
            self.y += self.vy * dt

            # Land on ground (triggers landing squish)
            if self.y >= GROUND_Y:
                self.y = float(GROUND_Y)
                self.vy = 0.0
                self.is_grounded = True
                self.squish_vy += profile["land_squash"] * 26.0

        # Running tilt / lean
        target_tilt = self.vx * profile["tilt_factor"]
        self.tilt += (target_tilt - self.tilt) * min(1.0, dt * 16.0)

        # Spring-damper integration for squish and impact dent
        k = profile["stiffness"]
        c = profile["damping"]

        # Sub-step spring simulation for guaranteed numerical stability
        sub_steps = 4
        s_dt = dt / sub_steps
        for _ in range(sub_steps):
            # Vertical squish oscillator: F = -k*y - c*vy
            ay = -k * self.squish_y - c * self.squish_vy
            self.squish_vy += ay * s_dt
            self.squish_y += self.squish_vy * s_dt

            # Impact dent oscillator (x and y)
            a_ix = -k * self.impact_x - c * self.impact_vx
            a_iy = -k * self.impact_y - c * self.impact_vy
            self.impact_vx += a_ix * s_dt
            self.impact_vy += a_iy * s_dt
            self.impact_x += self.impact_vx * s_dt
            self.impact_y += self.impact_vy * s_dt


class Ball:
    """Volleyball with 2D Newtonian physics, bounce restitution and spin."""

    def __init__(self, x: float, y: float):
        self.x: float = x
        self.y: float = y
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.rotation: float = 0.0       # Angle in radians
        self.angular_speed: float = 0.0  # Radians per second
        self.last_hit_by: Optional[int] = None  # 1 for left, 2 for right

    def reset(self, x: float, y: float, vx: float = 0.0, vy: float = 0.0) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.rotation = 0.0
        self.angular_speed = 0.0
        self.last_hit_by = None

    def update(self, dt: float) -> None:
        """Apply gravity and integrate position."""
        self.vy += BALL_GRAVITY * dt

        # Cap velocity to prevent tunneling or erratic behavior
        speed_sq = self.vx * self.vx + self.vy * self.vy
        if speed_sq > BALL_MAX_SPEED * BALL_MAX_SPEED:
            speed = math.sqrt(speed_sq)
            scale = BALL_MAX_SPEED / speed
            self.vx *= scale
            self.vy *= scale

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.angular_speed * dt

        # Air friction for spin
        self.angular_speed *= max(0.0, 1.0 - 0.4 * dt)


class PhysicsWorld:
    """Handles collision detection and resolution between ball, blobs, net, and bounds."""

    def __init__(self, blob_left: Blob, blob_right: Blob, ball: Ball):
        self.blob_left = blob_left
        self.blob_right = blob_right
        self.ball = ball

    def update(self, dt: float) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Sub-stepped physics update to guarantee collision stability.
        Returns:
            (hit_event_happened, hit_sound_name, ground_hit_side: 1 for left, 2 for right)
        """
        # Sub-stepping (2 steps per frame for high-speed ball precision)
        sub_steps = 2
        sub_dt = dt / sub_steps

        hit_sound: Optional[str] = None
        ground_hit_side: Optional[int] = None

        for _ in range(sub_steps):
            self.ball.update(sub_dt)

            # Check ball vs wall boundaries
            wall_hit = self._resolve_wall_collisions()
            if wall_hit and hit_sound is None:
                hit_sound = "bounce"

            # Check ball vs net
            net_hit = self._resolve_net_collision()
            if net_hit and hit_sound is None:
                hit_sound = "bounce"

            # Check ball vs left blob
            if self._resolve_blob_collision(self.blob_left, player_id=1):
                hit_sound = "hit"

            # Check ball vs right blob
            if self._resolve_blob_collision(self.blob_right, player_id=2):
                hit_sound = "hit"

            # Check ball vs ground
            if self.ball.y + BALL_RADIUS >= GROUND_Y:
                self.ball.y = float(GROUND_Y - BALL_RADIUS)
                ground_hit_side = 1 if self.ball.x < NET_X else 2
                hit_sound = "bounce"
                break

        return (hit_sound is not None, hit_sound, ground_hit_side)

    def _resolve_wall_collisions(self) -> bool:
        hit = False
        # Left wall
        if self.ball.x - BALL_RADIUS < 0:
            self.ball.x = float(BALL_RADIUS)
            self.ball.vx = abs(self.ball.vx) * BALL_RESTITUTION_WALL
            self.ball.angular_speed = -self.ball.vy * 0.05
            hit = True

        # Right wall
        elif self.ball.x + BALL_RADIUS > VIRTUAL_WIDTH:
            self.ball.x = float(VIRTUAL_WIDTH - BALL_RADIUS)
            self.ball.vx = -abs(self.ball.vx) * BALL_RESTITUTION_WALL
            self.ball.angular_speed = self.ball.vy * 0.05
            hit = True

        # Ceiling
        if self.ball.y - BALL_RADIUS < 0:
            self.ball.y = float(BALL_RADIUS)
            self.ball.vy = abs(self.ball.vy) * 0.8
            hit = True

        return hit

    def _resolve_net_collision(self) -> bool:
        """Resolve ball collision against the net post and rounded top cap."""
        ball = self.ball
        half_w = NET_WIDTH / 2.0
        net_left = NET_X - half_w
        net_right = NET_X + half_w

        # Quick AABB rejection
        if (
            ball.x + BALL_RADIUS < net_left
            or ball.x - BALL_RADIUS > net_right
            or ball.y + BALL_RADIUS < NET_TOP_Y
        ):
            return False

        # 1. Collision with rounded top cap of the net
        dx = ball.x - NET_X
        dy = ball.y - NET_TOP_Y
        dist_sq = dx * dx + dy * dy
        min_dist = BALL_RADIUS + half_w

        if dist_sq < min_dist * min_dist and dy <= 0:
            dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.001
            nx = dx / dist
            ny = dy / dist

            # Push out
            overlap = min_dist - dist
            ball.x += nx * overlap
            ball.y += ny * overlap

            # Reflect velocity
            dot = ball.vx * nx + ball.vy * ny
            if dot < 0:
                restitution = BALL_RESTITUTION_NET
                ball.vx -= (1.0 + restitution) * dot * nx
                ball.vy -= (1.0 + restitution) * dot * ny
                ball.angular_speed += nx * 5.0
            return True

        # 2. Side collisions against vertical post (below net top)
        if ball.y >= NET_TOP_Y:
            if ball.x < NET_X and ball.x + BALL_RADIUS > net_left:
                ball.x = float(net_left - BALL_RADIUS)
                ball.vx = -abs(ball.vx) * BALL_RESTITUTION_NET
                ball.angular_speed -= 4.0
                return True
            elif ball.x >= NET_X and ball.x - BALL_RADIUS < net_right:
                ball.x = float(net_right + BALL_RADIUS)
                ball.vx = abs(ball.vx) * BALL_RESTITUTION_NET
                ball.angular_speed += 4.0
                return True

        return False

    def _resolve_blob_collision(self, blob: Blob, player_id: int) -> bool:
        """
        Collide ball with capsule/dome of the blob.
        Head dome center is (blob.x, blob.y - BLOB_BODY_HEIGHT).
        Segment goes from head center to (blob.x, blob.y - BLOB_RADIUS).
        """
        ball = self.ball

        # Vertical segment representing the center axis of the blob
        seg_x = blob.x
        seg_top_y = blob.y - BLOB_BODY_HEIGHT
        seg_bot_y = blob.y - (BLOB_RADIUS * 0.4)

        # Find closest point on vertical segment to the ball
        closest_x = seg_x
        closest_y = max(seg_top_y, min(ball.y, seg_bot_y))

        dx = ball.x - closest_x
        dy = ball.y - closest_y
        dist_sq = dx * dx + dy * dy
        min_dist = BALL_RADIUS + BLOB_RADIUS

        if dist_sq >= min_dist * min_dist:
            return False

        dist = math.sqrt(dist_sq) if dist_sq > 0 else 0.001
        nx = dx / dist
        ny = dy / dist

        # Separate ball from blob
        overlap = min_dist - dist
        ball.x += nx * overlap
        ball.y += ny * overlap

        # Relative velocity
        rel_vx = ball.vx - blob.vx
        rel_vy = ball.vy - blob.vy
        vel_norm = rel_vx * nx + rel_vy * ny

        # Only bounce if approaching
        if vel_norm < 0:
            # Trigger squishy impact deformation on blob
            impact_speed = max(180.0, abs(vel_norm))
            blob.apply_impact(nx, ny, impact_speed)

            # Energetic bounce with player impulse transfer
            restitution = 1.08
            impulse = -(1.0 + restitution) * vel_norm

            ball.vx += impulse * nx + blob.vx * 0.35
            ball.vy += impulse * ny + min(0.0, blob.vy * 0.35)

            # Ensure minimum bounce velocity upward/outward
            current_speed = math.sqrt(ball.vx * ball.vx + ball.vy * ball.vy)
            if current_speed < BALL_MIN_BOUNCE:
                ball.vy = min(ball.vy, -BALL_MIN_BOUNCE * 0.8)
                if abs(ball.vx) < 50.0:
                    ball.vx = 100.0 if blob.is_left else -100.0

            # Spin from tangential impact
            tangent_speed = -rel_vx * ny + rel_vy * nx
            ball.angular_speed = -tangent_speed * 0.06

        ball.last_hit_by = player_id
        blob.touches += 1
        return True
