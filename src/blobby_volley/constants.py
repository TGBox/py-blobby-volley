"""Constants, dimensions, physical properties and color palettes."""

# Virtual screen resolution for fixed aspect-ratio rendering
VIRTUAL_WIDTH = 800
VIRTUAL_HEIGHT = 600
TARGET_FPS = 60

# Court layout
GROUND_Y = 500
NET_X = 400
NET_WIDTH = 14
NET_HEIGHT = 180
NET_TOP_Y = GROUND_Y - NET_HEIGHT

# Blob dimensions & physics
BLOB_RADIUS = 36          # Radius of the head dome & horizontal half-width
BLOB_BODY_HEIGHT = 50     # Height of the body below the dome center
BLOB_TOTAL_HEIGHT = BLOB_RADIUS + BLOB_BODY_HEIGHT
BLOB_SPEED = 330.0        # Horizontal move speed in px/sec
BLOB_JUMP_SPEED = -580.0  # Initial jump velocity in px/sec
BLOB_GRAVITY = 1200.0     # Gravity acceleration for blobs

# Jelly squish & spring-damper deformation profiles
JELLY_PROFILES = {
    "Normal": {
        "stiffness": 160.0,       # Spring stiffness (k)
        "damping": 14.0,          # Damping coefficient (c)
        "jump_stretch": 0.30,     # Vertical elongation on jump
        "land_squash": -0.35,     # Vertical compression on landing
        "impact_strength": 0.35,  # Ball impact compression multiplier
        "tilt_factor": 0.00036,   # Forward lean angle in radians per px/s
        "max_deformation": 0.50,  # Clamp on deviation from 1.0
    },
    "Extrem": {
        "stiffness": 80.0,        # Lower stiffness for softer jiggle
        "damping": 5.5,           # Low damping for prolonged wobble
        "jump_stretch": 0.55,     # Huge stretch
        "land_squash": -0.55,     # Huge squash
        "impact_strength": 0.70,  # Extreme impact dent
        "tilt_factor": 0.00065,   # Heavy lean
        "max_deformation": 0.75,  # Allows big elastic distortion
    },
}

# Ball dimensions & physics
BALL_RADIUS = 20
BALL_GRAVITY = 680.0
BALL_MAX_SPEED = 900.0
BALL_MIN_BOUNCE = 200.0
BALL_RESTITUTION_WALL = 0.92
BALL_RESTITUTION_NET = 0.75
BALL_RESTITUTION_GROUND = 0.82

# Serve positions
SERVE_LEFT_X = 200.0
SERVE_RIGHT_X = 600.0
SERVE_BALL_Y = 220.0

# Gameplay rules
POINTS_TO_WIN = 15
MAX_TOUCHES = 3

# AI Difficulty settings
AI_DIFFICULTIES = {
    "Leicht": {"reaction_delay": 0.16, "jitter": 32.0, "jump_chance": 0.65},
    "Mittel": {"reaction_delay": 0.08, "jitter": 14.0, "jump_chance": 0.88},
    "Schwer": {"reaction_delay": 0.02, "jitter": 3.0, "jump_chance": 0.98},
}

# Color definitions
COLOR_SKY_TOP = (41, 128, 185)
COLOR_SKY_BOTTOM = (109, 213, 250)
COLOR_SEA = (26, 82, 118)
COLOR_SEA_LIGHT = (46, 134, 193)
COLOR_SAND = (244, 208, 63)
COLOR_SAND_DARK = (212, 172, 13)
COLOR_NET_POST = (189, 195, 199)
COLOR_NET_MESH = (236, 240, 241)
COLOR_NET_TOP = (231, 76, 60)

COLOR_BLOB_LEFT = (46, 204, 113)        # Classic green
COLOR_BLOB_LEFT_DARK = (39, 174, 96)
COLOR_BLOB_RIGHT = (231, 76, 60)        # Classic red/orange
COLOR_BLOB_RIGHT_DARK = (192, 57, 43)

COLOR_EYE_WHITE = (255, 255, 255)
COLOR_EYE_PUPIL = (44, 62, 80)
COLOR_BALL_WHITE = (255, 255, 255)
COLOR_BALL_STRIPE1 = (241, 196, 15)     # Yellow
COLOR_BALL_STRIPE2 = (52, 152, 219)     # Blue
COLOR_SHADOW = (0, 0, 0, 70)
COLOR_TEXT = (255, 255, 255)
COLOR_TEXT_SHADOW = (20, 20, 20)
COLOR_HUD_BG = (20, 30, 45, 160)
