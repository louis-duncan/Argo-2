ADDRESS = "home.ltcomputing.co.uk"
SEND_PORT = 31416
GET_PORT = 31417

DIRECTIONS = ("n", "ne", "e", "se", "s", "sw", "w", "nw")
COLOURS = ("red", "green", "blue", "yellow", "white", "black")
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
