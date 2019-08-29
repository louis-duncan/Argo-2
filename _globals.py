ADDRESS = "home.ltcomputing.co.uk"
SEND_PORT = 31416
GET_PORT = 31417

DIRECTIONS = ("n", "ne", "e", "se", "s", "sw", "w", "nw")
COLOURS = ("red", "green", "blue", "yellow", "white", "black")
SERVER_COMMANDS = {"create": ("type", "colour(red|blue|green|yellow|white|black)"),
                   "destroy": ("leave_debris(True|False)",),
                   "set_pos": ("x(0-w)", "y(0-h)"),
                   "move": ("n|ne|e|se|s|sw|w|nw|f",),
                   "face": ("n|ne|e|se|s|sw|w|nw|l|r",),
                   "hide": tuple(),
                   "show": tuple(),
                   "send_msg": ("message",),
                   "set_stat": ("system_name", "up|down"),
                   "reset": tuple(),
                   }
