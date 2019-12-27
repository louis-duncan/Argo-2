from _classes import *

main_game = Game()
main_game.create_entity(
    {
        "type": "ship",
        "name": "Aloha Oe",
        "colour": "blue",
        "pos": (5, 6),
        "direction": 1,
        "ttl": None
    },
    "local"
)
