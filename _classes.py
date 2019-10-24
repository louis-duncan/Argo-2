import random
import time
import queue
import socket
import threading
import json
import logging
import sys
from _globals import *


# noinspection SpellCheckingInspection
logging.basicConfig(
    filename="server_log.log",
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%d/%m/%Y %I:%M:%S %p',
    level=logging.DEBUG
)


class Clock:
    def __init__(self):
        self._last_tick_time = 0

    def tick(self, rate):
        delay = (self._last_tick_time + (1 / rate)) - time.time()
        if delay < 0:
            delay = 0
        time.sleep(delay)
        self._last_tick_time = time.time()


class Game:
    def __init__(self):
        self.entities = []
        self.events_queue = queue.SimpleQueue()

        self.Communicator = ServerCommunicator(self, SERVER_ADDR)

        self._tick_thread = threading.Thread(target=self.tick_loop, args=tuple())
        self._tick_thread.start()

    def get_entities(self, pos):
        results = []
        for e in self.entities:
            if e.pos[0] == pos[0] and e.pos[1] == pos[1]:
                results.append(e)
        return results

    def tick_loop(self, rate=30):
        clock = Clock()
        while True:
            self.handle_events()
            for e in self.entities:
                e.tick()
            clock.tick(rate)

    def handle_events(self):
        event: dict
        for event in range(self.events_queue.qsize()):
            print(self.events_queue.get())

            try:
                if event["action"] == "move":
                    pass
                elif event["action"] == "turn":
                    pass
                elif event["action"] == "destroy":
                    pass
                elif event["action"] == "fire_weapon":
                    pass
                else:
                    print("Unknown action", event["action"])
            except KeyError as err:
                print("Bad key:", err.args[0])

    def get_state(self):
        return {"entities": self.entities}


class Entity:
    def __init__(self,
                 parent=None,
                 entity_id=ANY_ID,
                 name="no_name",
                 colour=BLACK,
                 pos=(0, 0),
                 facing=NORTH,
                 created_by=None,
                 created_time=None,
                 ttl=None,
                 **kwargs):
        self.parent = parent
        self.entity_id = entity_id
        self.name = name
        self.colour = colour
        self.pos = pos
        self.facing = facing
        self.created_by = created_by
        if created_time is None:
            self.created_time = time.time()
        self.ttl = ttl

        if self.entity_id is None:
            self.entity_id = random.randint(10000, 99999)

    def destroy(self):
        self.parent.entities.remove(self)

    def move(self, direction=FORWARD):
        assert direction in (FORWARD, BACKWARD)

        if self.facing in (NORTH, NORTH_WEST, NORTH_EAST):
            self.pos[0] -= direction
        elif self.facing in (SOUTH, SOUTH_WEST, SOUTH_EAST):
            self.pos[0] += direction

        if self.facing in (WEST, NORTH_WEST, SOUTH_WEST):
            self.pos[1] -= direction
        elif self.facing in (EAST, NORTH_EAST, SOUTH_EAST):
            self.pos[1] += direction

    def turn(self, direction):
        assert direction in (LEFT, RIGHT)
        self.facing = DIRECTIONS[(DIRECTIONS.index(self.facing) + direction) % len(DIRECTIONS)]

    def tick(self):
        if (self.ttl is not None) and (self.created_time + self.ttl >= time.time()):
            self.destroy()


class Ship(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.trail_ttl = 60
        self.reactor_overload = False
        self.shields_level = 0
        self.hull_hp = 24

        self.systems = [
            ShipSystem("Reactor_Output"),
            ShipSystem("Shields"),
            ShipSystem("Weapons"),
            ShipSystem("Life_Support"),
            ShipSystem("Holograms")
        ]

        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def _spawn_trail(self, pos=None):
        if pos is None:
            pos = self.pos
        self.parent.entities.append(
            Trail(
                parent=self.parent,
                colour=self.colour,
                pos=pos,
                facing=self.facing,
                created_by=self,
                ttl=self.trail_ttl
            )
        )

    def _spawn_debris(self, pos=None):
        if pos is None:
            pos = self.pos
        self.parent.entities.append(
            Debris(
                parent=self.parent,
                colour=self.colour,
                pos=pos,
                created_by=self
            )
        )

    def move(self, direction=FORWARD):
        self._spawn_trail()
        super().move(direction)

    def get_states(self):
        return {s.name: s.level() for s in self.systems}

    def destroy(self):
        self._spawn_debris()
        super().destroy()


class ShipSystem:
    def __init__(self, name, level=0, max_level=8, modifiers=None, **kwargs):
        self.name = name
        self._level = level
        self.max_level = max_level
        if modifiers is None:
            self.modifiers = list()
        else:
            self.modifiers = modifiers

    def level(self, lvl=None):
        if lvl is not None:
            self._level = lvl
            return
        result = self._level
        m = 0
        while m < len(self.modifiers):
            if self.modifiers[m].expiry < time.time():
                self.modifiers.remove(self.modifiers[m])
            else:
                result += self.modifiers[m].amount
                m += 1
        return result


class SystemModifier:
    def __init__(self, amount, ttl, expiry=None, **kwargs):
        self.amount = amount
        self.ttl = ttl
        if expiry is None:
            self.expiry = time.time() + ttl
        else:
            self.expiry = expiry


class Trail(Entity):
    def __init__(self, **kwargs):
        super().__init__(kwargs)


class Debris(Entity):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._last_turn_time = 0
        self._turn_interval = 2

    def tick(self):
        if self._last_turn_time + self._turn_interval < time.time():
            self.turn(RIGHT)
            self._last_turn_time = time.time()
        super().tick()


class Station(Entity):
    def __init__(self, **kwargs):
        super().__init__(kwargs)
        self._last_turn_time = 0
        self._turn_interval = 3

    def tick(self):
        if self._last_turn_time + self._turn_interval < time.time():
            self.turn(RIGHT)
            self._last_turn_time = time.time()
        super().tick()


class CommunicationError(Exception):
    pass


class ServerCommunicator:
    def __init__(self, parent, addr):
        self.parent = parent
        self._addr = addr

        self.errors = []
        self.msg_size_limit = 1024

        self._server_socket = socket.socket()
        self._server_socket.bind(self._addr)
        self._server_socket.listen(5)

        self._connection_threads = []
        self._connection_sockets = []
        self._receiver = threading.Thread(target=self.thread_runner, args=(self.connection_receiver, tuple()))
        self._receiver.start()

    def thread_runner(self, target, args):
        try:
            target(*args)
        except Exception as e:
            self.errors.append(sys.exc_info())
            logging.warning('Exception "{}" occurred in TCP/IP thread.'.format(type(e)))
            self.errors.append(e)

    def connection_receiver(self):
        while True:
            con, addr = self._server_socket.accept()
            logging.info("New connection received from {}.".format(con.getpeername()))
            new = threading.Thread(target=self.thread_runner, args=(self.client_handler, (con,)))
            self._connection_threads.append(new)
            new.start()

    def client_handler(self, con):
        """

        :type con: socket.socket
        """
        self._connection_sockets.append(con)
        peer_name = con.getpeername()

        try:
            run = True
            while run:
                msg_len = con.recv(2)
                if msg_len == b"":
                    logging.info("Client {} closed its connection.".format(peer_name))
                    self._connection_sockets.remove(con)
                    break

                msg_len = (msg_len[0] * 256) + msg_len[1]

                if msg_len > self.msg_size_limit:
                    logging.warning("Client {} sent a message over the size limit ({}/{}).".format(
                        peer_name,
                        msg_len,
                        self.msg_size_limit
                    ))
                    con.close()
                    self._connection_sockets.remove(con)
                    logging.info("Connection with {} closed due to violation.".format(peer_name))
                    run = False
                    continue

                msg_data = con.recv(msg_len).decode()
                if len(msg_data) != msg_len:
                    logging.warning("Client {} sent a runt message (length: {}).".format(
                        peer_name,
                        msg_len
                    ))
                    con.close()
                    self._connection_sockets.remove(con)
                    logging.info("Connection with {} closed due to violation.".format(peer_name))
                    run = False
                    continue

                try:
                    msg_data = json.loads(msg_data)
                    if type(msg_data) is not dict:
                        raise TypeError
                except json.decoder.JSONDecodeError:

                    logging.warning("Client {} sent a message of invalid format.".format(peer_name))
                    con.close()
                    self._connection_sockets.remove(con)
                    logging.info("Connection with {} closed due to violation.".format(peer_name))
                    run = False
                    continue
                except TypeError:
                    logging.warning("Client {} sent a message of invalid type.".format(peer_name))
                    con.close()
                    self._connection_sockets.remove(con)
                    logging.info("Connection with {} closed due to violation.".format(peer_name))
                    run = False
                    continue

                if "action" in msg_data.keys() and msg_data["action"] == "update_request":
                    self.send_data(con, self.parent.get_state())
                else:
                    self.parent.events_queue.put(msg_data)

        except Exception as e:
            try:
                self._connection_sockets.remove(con)
            except ValueError:
                pass
            raise e

    def send_data(self, con, data):
        raw_data = json.dumps(make_json_friendly(data)).encode()
        len_bytes = bytes([len(raw_data) // 256, len(raw_data) % 256])
        con.send(len_bytes)
        con.send(raw_data)


class ClientCommunicator(socket.socket):
    def object_send(self, data):
        raw = json.dumps(data).encode()
        len_bytes = bytes([len(raw) // 256, len(raw) % 256])
        super().send(len_bytes)
        super().send(raw)

    def object_recv(self):
        msg_len = self.recv(2)
        if msg_len == b"":
            return
        received_bytes = self.recv((msg_len[0] * 256) + msg_len[1])
        return object_from_decoded_json(json.loads(received_bytes.decode()), None)


def create_client_connection(addr):
    con = ClientCommunicator()
    con.connect(addr)
    return con


def make_json_friendly(o):
    """Take an object and converts it to a JSON compatible object.
    Any object (o) which is not a standard data type will be converted to a dict
    with the __type__ key specifying the objects original type."""
    if type(o) in (str, int, float, bool, type(None)):
        new_o = o
    elif type(o) is dict:
        new_o = dict()
        for k in o:
            new_o[k] = make_json_friendly(o[k])
    elif type(o) in (list, tuple):
        new_o = list(o)
        for i in range(len(new_o)):
            new_o[i] = make_json_friendly(new_o[i])
    else:
        new_o = dict(o.__dict__)
        if "parent" in new_o.keys():
            r = new_o.pop("parent")
        new_o["__type__"] = type(o).__name__
        new_o = make_json_friendly(new_o)
    return new_o


def object_from_decoded_json(o, parent=None):
    if type(o) is dict:
        if "__type__" in o.keys():
            o_type = o.pop("__type__")
            kwargs = object_from_decoded_json(o)
            new_object = globals()[o_type](parent=parent, **kwargs)
        else:
            new_object = {key: object_from_decoded_json(value) for (key, value) in o.items()}
    elif type(o) in (str, int, float, bool, type(None)):
        new_object = o
    elif type(o) in (list, tuple):
        new_object = [object_from_decoded_json(i) for i in o]
    else:
        new_object = None
    return new_object
