import json
import random
import socket
import threading
import time
from _globals import *

ADDRESS = ("localhost", 1234)


class EventError(Exception):
    pass


class GameEvent:
    def __init__(self, source, action=None, target=None, args=None, raw=None):
        self.source = source

        if target is None:
            target = ""
        if action is None:
            action = ""
        if args is None:
            args = list()
        if raw is None:
            raw = dict()

        if target != "" or action != "":
            self.target = target
            self.action = action
            self.args = args
        else:
            if type(raw) is dict:
                pass
            elif type(raw) is str:
                try:
                    raw = json.loads(raw)
                    if not (type(raw) is dict):
                        raise (EventError("Could not convert event data of type " + str(type(raw))))
                except json.JSONDecodeError:
                    raise EventError("Invalid JSON data from string.")
            elif type(raw) is bytes:
                try:
                    raw = raw.decode()
                    raw = json.loads(raw)
                except json.JSONDecodeError:
                    raise EventError("Invalid JSON data from bytes.")
            else:
                raise (EventError("Could not convert event data of type " + str(type(raw))))

            try:
                self.target = raw["target"]
            except KeyError:
                raise EventError("Event data missing 'target' information.")

            try:
                action_parts = raw["action"].split(" ")
                self.action = action_parts[0].lower()
                self.args = action_parts[1:]
                if not (self.action in SERVER_COMMANDS.keys()):
                    raise EventError("Unknown command '{}'".format(self.action))
            except KeyError:
                raise EventError("Event data missing 'action' information.")

            try:
                if type(raw["args"]) is str:
                    raw["args"] = raw["args"].split(" ")
                self.args += raw["args"]
            except KeyError:
                pass

            for a in range(len(self.args)):
                self.args[a] = self.args[a].lower()

            if len(self.args) != len(SERVER_COMMANDS[self.action]):
                raise EventError("Invalid number of arguments given. {} expected, {} given.".format(
                    len(SERVER_COMMANDS[self.action]),
                    len(self.args))
                                 )

        self.time = time.time()

    def __repr__(self):
        return "{} - source: {}, target: {},  action: {}, args: {}".format(time.ctime(self.time),
                                                                           self.source,
                                                                           self.target,
                                                                           self.action,
                                                                           self.args)


class ConnectionHandler:
    def __init__(self, con, queue):
        self.closed = False
        self.peer_name = con.getpeername()
        self.con = con
        self.log = []

        self.thread = threading.Thread(target=self.run, args=(queue,))
        self.thread.start()

    def run(self, queue):
        self.log.append("Listening to " + str(self.peer_name))
        received = ""
        new = None
        try:
            while new != b"" and not self.closed:
                new = self.con.recv(32)
                if new != b"":
                    received += new.decode()
                    while "\n" in received:
                        parts = received.split("\n", 1)
                        received = parts[1]
                        try:
                            event = GameEvent(self.con.getpeername(), raw=parts[0])
                            queue.append(event)
                        except EventError as e:
                            self.log.append("EventError: " + e.args[0])
            self.con.close()
        except ConnectionError:
            pass
        except OSError:
            pass
        self.log.append(str(self.peer_name) + " has closed")
        self.closed = True

    def send(self, data):
        return self.con.send(data)


class ConnectionManager:
    def __init__(self):
        self.action_button_limit = 255
        self.action_queue = []
        self.connections = {}
        self.game_state = {}

        self.running = True

        listener_thread = threading.Thread(target=self.listener, args=tuple())
        listener_thread.start()
        maintainer_thread = threading.Thread(target=self.maintainer, args=tuple())
        maintainer_thread.start()

    def listener(self):
        server_socket = socket.socket()
        server_socket.bind(ADDRESS)
        server_socket.listen(5)
        while self.running:
            con, addr = server_socket.accept()
            self.connections[addr] = ConnectionHandler(con, self.action_queue)

    def maintainer(self):
        """loop through the connections and send the game state to them.
        If the connection is closed, garbage collect it.
        :return:
        """
        while self.running:
            if len(self.action_queue) >= self.action_button_limit:
                time.sleep(1)
            else:
                state = json.dumps(self.game_state).encode()
                keys = list(self.connections.keys())
                for k in keys:
                    for i in range(len(self.connections[k].log)):
                        print(self.connections[k].log.pop(0))

                    if self.connections[k].closed:
                        self.connections.pop(k)
                    else:
                        try:
                            self.connections[k].send(state)
                        except OSError:
                            pass

    def get_actions(self):
        output = []
        for i in range(len(self.action_queue)):
            output.append(self.action_queue.pop(0))
        return output


class GameObject:
    def __init__(self, name, colour, pos, facing, creator="console"):
        assert colour in COLOURS
        self.name = name
        self.colour = colour
        self.pos = pos
        self.facing = facing
        self.pushes = False
        self.can_be_pushed = False
        self.destroyed = False
        self.hidden = False
        self.leaves_trail = False
        self.creator = creator

    def move(self, direction):
        if direction == "f":
            direction = self.facing

        if "n" in direction:
            self.pos = (self.pos[0], self.pos[1] - 1)
        if "e" in direction:
            self.pos = (self.pos[0] + 1, self.pos[1])
        if "s" in direction:
            self.pos = (self.pos[0], self.pos[1] + 1)
        if "w" in direction:
            self.pos = (self.pos[0] - 1, self.pos[1])

    def set_pos(self, x, y):
        self.pos = (x, y)

    def face(self, direction):
        if direction == "l":
            direction = DIRECTIONS[(DIRECTIONS.index(self.facing) - 1) % len(DIRECTIONS)]
        if direction == "r":
            direction = DIRECTIONS[(DIRECTIONS.index(self.facing) + 1) % len(DIRECTIONS)]
        self.facing = direction

    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False

    def destroy(self, leave_debris=False):
        if type(leave_debris) == str:
            if not (leave_debris.lower() in ("true", "false")):
                raise TypeError("'{}' cannot be converted to bool.".format(leave_debris))
            leave_debris = leave_debris.lower() == "true"
        self.destroyed = True
        self.hidden = not leave_debris

    def tick(self):
        # All per/tick updates to happen here.
        pass


class Ship(GameObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.reactor = ShipSystem("reactor", 0, 24, 12)
        self.systems = {}

        self.in_overload = False
        self.overload_trigger_time = 0
        self.overload_cool_down_time = 10
        self.message = None
        self.message_recv_time = 0
        self.message_display_time = 10
        self.leaves_trail = True
        self.pushes = True
        self.can_be_pushed = True

    def set_stat(self, system_name, change):
        if (self.systems is None) or not (system_name in self.systems.keys()):
            return
        if change == "up":
            if self.systems[system_name].can_increase():
                if self.reactor.can_decrease():
                    self.systems[system_name].increase()
                    self.reactor.decrease()
                else:
                    self.trigger_overload()
        elif change == "down":
            if self.systems[system_name].can_decrease():
                self.systems[system_name].decrease()
                self.reactor.increase()
        else:
            pass

    def add_system(self, system):
        self.systems[system.name] = system

    def send_msg(self, message):
        self.message = message
        self.message_recv_time = time.time()

    def trigger_overload(self):
        self.in_overload = True
        self.overload_trigger_time = time.time()

    def spawn_trail(self):
        pass

    def tick(self):
        super().tick()

        # Check overload state.
        if time.time() > self.overload_trigger_time + self.overload_cool_down_time:
            self.in_overload = False

        # Check if message should still exist.
        if self.message is not None and (self.message_recv_time + self.message_display_time) < time.time():
            self.message = None


class ShipSystem:
    def __init__(self, name, min_level=0, max_level=8, default=0, reset_action="default"):
        self.name = name
        self.min_level = min_level
        self.max_level = max_level
        self.default = default
        self.level = default
        self.reset_action = reset_action

    def increase(self, val=1):
        if self.level + val <= self.max_level:
            self.level += val
            return True

    def decrease(self, val=1):
        if self.level - val >= self.min_level:
            self.level -= val

    def reset(self):
        if self.reset_action == "default":
            self.level = self.default
        elif self.reset_action == "min":
            self.level = self.min_level
        elif self.reset_action == "max":
            self.level = self.max_level
        else:
            pass

    def can_increase(self, val=1):
        return self.level + val <= self.max_level

    def can_decrease(self, val=1):
        return self.level - val >= self.min_level


class Trail(GameObject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)



    def tick(self):
        super().tick()
        self.


class Game:
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.running = True
        self.game_objects = {}

        action_thread = threading.Thread(target=self.action_handler, args=tuple())
        action_thread.start()

    def action_handler(self):
        while self.running:
            a: GameEvent
            for a in self.connection_manager.get_actions():
                if a.action == "create":
                    self.add_game_object(a.target,
                                         a.args[0],
                                         a.args[1])
                elif a.action == "move":
                    target_object = self.game_objects[a.target]
                    try:
                        new_obj = target_object.spawn_trail()
                        self.game_objects[new_obj.name] = new_obj
                    except AttributeError:
                        pass

                    self.game_objects[a.target].move(*a.args)

                else:
                    try:
                        # Try to run the method of the game object with the name of the action.
                        getattr(self.game_objects[a.target], a.action)(*a.args)
                    except AttributeError:
                        pass

    def add_game_object(self, name, obj_type, colour, creator="", pos=(0, 0), direction="n"):
        if name in self.game_objects.keys():
            return False
        if not (colour in COLOURS):
            return False
        if obj_type == "ship":
            self.game_objects[name] = Ship(name,
                                           colour,
                                           (0, 0),
                                           "n",
                                           creator)
            # Add ship systems.
            self.game_objects[name].add_system(ShipSystem("fw_shield",
                                                          0,
                                                          6,
                                                          0))
            # More systems here.
        elif obj_type == "something else":
            pass  # Make the things.
        else:
            return False


game = Game()
