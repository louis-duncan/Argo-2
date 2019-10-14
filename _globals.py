ADDRESS = "home.ltcomputing.co.uk"
SEND_PORT = 31416
GET_PORT = 31417

ANY_ID = None

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
