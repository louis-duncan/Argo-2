import os

SERVER_ADDR = ("localhost", 1234)  # ("home.ltcomputing.co.uk", 31416)

ANY_ID = None
ID_UP = 31415
ID_RIGHT = 31416
ID_DOWN = 31417
ID_LEFT = 31418
ID_DELETE = 31419
ID_ALL = 31420
ID_NONE = 31421
ID_CREATE = 31422
OBJECT_BUTTON_ID = 98765

GRID_SIZE = 20

INCREASE = 1
DECREASE = -1

NORTH = 0
NORTH_EAST = 1
EAST = 2
SOUTH_EAST = 3
SOUTH = 4
SOUTH_WEST = 5
WEST = 6
NORTH_WEST = 7

FORWARD = 1
BACKWARD = -1
RIGHT = 1
LEFT = -1

DIRECTIONS = (
    NORTH,
    NORTH_EAST,
    EAST,
    SOUTH_EAST,
    SOUTH,
    SOUTH_WEST,
    WEST,
    NORTH_WEST
)

DIRECTION_TRANSLATIONS = {
    "n": NORTH,
    "ne": NORTH_EAST,
    "e": EAST,
    "se": SOUTH_EAST,
    "s": SOUTH,
    "sw": SOUTH_WEST,
    "w": WEST,
    "nw": NORTH_WEST
}

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GREY = (120, 120, 120)
LIGHT_GREY = (220, 220, 220)

COLOURS = {
    "red": RED,
    "green": GREEN,
    "blue": BLUE,
    "yellow": YELLOW,
    "white": WHITE,
    "black": BLACK
}

SERVER_COMMANDS = {"create": ("type", "colour(red|blue|green|yellow|white|black)",
                              "x_pos(0-19)", "y_pos(0-19)", "direction(n|ne|e|se|s|sw|w|nw)"),
                   "destroy": ("leave_debris(true|false)",),
                   "set_pos": ("x(0-w)", "y(0-h)"),
                   "move": ("n|ne|e|se|s|sw|w|nw|f",),
                   "face": ("n|ne|e|se|s|sw|w|nw|l|r",),
                   "hide": tuple(),
                   "show": tuple(),
                   "send_msg": ("message",),
                   "set_stat": ("system_name", "up|down"),
                   "reset": tuple(),
                   }

GAME_OBJECT_TYPES = ("ship",
                     "trail",
                     "station",
                     "rock",
                     "anomaly")

SPRITE_DIR = "sprites"
UNKNOWN_SPRITE = os.path.abspath(os.path.join(SPRITE_DIR, "unknown.png"))
ERROR_SPRITE = os.path.abspath(os.path.join(SPRITE_DIR, "error.png"))
GRID_SPRITE = os.path.abspath(os.path.join(SPRITE_DIR, "grid.png"))


def get_sprite_path(object_type, colour):
    path = os.path.join(
        SPRITE_DIR,
        "{}_{}.png".format(
            object_type.lower(),
            colour.lower()
        )
    )
    if os.path.exists(path):
        return os.path.abspath(path)
    else:
        return os.path.abspath(ERROR_SPRITE)