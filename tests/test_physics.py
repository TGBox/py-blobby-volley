"""Unit tests for Blobby Volley physics, collisions, and scoring rules."""

import unittest
from blobby_volley.constants import (
    GROUND_Y,
    NET_X,
    NET_WIDTH,
    NET_TOP_Y,
    BLOB_RADIUS,
    BALL_RADIUS,
    POINTS_TO_WIN,
    SERVE_LEFT_X,
    SERVE_RIGHT_X,
    SERVE_BALL_Y,
)
from blobby_volley.physics import Blob, Ball, PhysicsWorld
from blobby_volley.game import GameState


class TestBlobPhysics(unittest.TestCase):
    def test_blob_boundary_clamping(self):
        blob_left = Blob(x=200, is_left=True)
        # Try moving far left off-screen
        blob_left.update(dt=10.0, move_dir=-1.0, jump_pressed=False)
        self.assertGreaterEqual(blob_left.x, BLOB_RADIUS)

        # Try moving across the net
        blob_left.update(dt=10.0, move_dir=1.0, jump_pressed=False)
        self.assertLessEqual(blob_left.x, NET_X - (NET_WIDTH / 2.0) - BLOB_RADIUS)

    def test_blob_jump_and_landing(self):
        blob = Blob(x=200, is_left=True)
        self.assertTrue(blob.is_grounded)
        self.assertEqual(blob.y, GROUND_Y)

        # Jump
        blob.update(dt=0.016, move_dir=0.0, jump_pressed=True)
        self.assertFalse(blob.is_grounded)
        self.assertLess(blob.vy, 0)  # Upward velocity

        # Simulate until landing
        for _ in range(120):
            blob.update(dt=0.016, move_dir=0.0, jump_pressed=False)
        self.assertTrue(blob.is_grounded)
        self.assertEqual(blob.y, GROUND_Y)
        self.assertEqual(blob.vy, 0.0)


class TestBallAndCollision(unittest.TestCase):
    def test_ball_wall_bounce(self):
        blob_l = Blob(200, is_left=True)
        blob_r = Blob(600, is_left=False)
        ball = Ball(x=BALL_RADIUS + 5, y=300)
        ball.vx = -300.0  # Heading towards left wall
        world = PhysicsWorld(blob_l, blob_r, ball)

        hit, sound, ground = world.update(dt=0.05)
        self.assertTrue(hit)
        self.assertEqual(sound, "bounce")
        self.assertGreater(ball.vx, 0)  # Bounced rightward

    def test_ball_blob_collision(self):
        blob_l = Blob(200, is_left=True)
        blob_r = Blob(600, is_left=False)
        # Position ball right above left blob's head
        head_x, head_y = blob_l.head_center
        ball = Ball(x=head_x, y=head_y - BLOB_RADIUS - BALL_RADIUS + 5)
        ball.vy = 200.0  # Falling down into head
        world = PhysicsWorld(blob_l, blob_r, ball)

        hit, sound, ground = world.update(dt=0.016)
        self.assertTrue(hit)
        self.assertEqual(sound, "hit")
        self.assertLess(ball.vy, 0)  # Bounced upwards
        self.assertEqual(blob_l.touches, 1)


class TestGameRules(unittest.TestCase):
    def test_side_out_and_scoring(self):
        game = GameState(mode="2p_local")
        self.assertEqual(game.server, 1)
        self.assertEqual(game.score_left, 0)
        self.assertEqual(game.score_right, 0)

        # Server 1 serves, ball lands on right side (loser = 2)
        # Since server 1 won rally, server 1 gets a point!
        game._handle_rally_end(loser=2)
        self.assertEqual(game.score_left, 1)
        self.assertEqual(game.server, 1)

        # Now ball lands on left side (loser = 1)
        # Server 1 loses rally -> Side-out (Player 2 gets serve, but no point yet)
        game._handle_rally_end(loser=1)
        self.assertEqual(game.score_left, 1)
        self.assertEqual(game.score_right, 0)
        self.assertEqual(game.server, 2)

        # Now server 2 wins rally (loser = 1) -> Player 2 gets a point!
        game._handle_rally_end(loser=1)
        self.assertEqual(game.score_right, 1)
        self.assertEqual(game.server, 2)

    def test_match_victory_condition(self):
        game = GameState(mode="vs_bot")
        game.score_left = POINTS_TO_WIN - 1  # 14 points
        game.score_right = 10
        game.server = 1

        game._handle_rally_end(loser=2)  # Score 15:10
        self.assertEqual(game.score_left, 15)
        self.assertTrue(game.match_over)
        self.assertEqual(game.winner, 1)

    def test_headless_smoke_simulation(self):
        """Simulate 200 ticks of full game without GUI to ensure no crashes."""
        game = GameState(mode="vs_bot")
        for _ in range(200):
            game.update(dt=0.016, p1_dir=1.0, p1_jump=False)
        self.assertIsNotNone(game.ball.x)


if __name__ == "__main__":
    unittest.main()
