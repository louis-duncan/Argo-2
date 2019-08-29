import json
import socket
import threading
import time

ADDRESS = ("localhost", 1234)


class EventError(Exception):
    pass


class GameEvent:
    def __init__(self, source, target=None, action=None, raw=None):
        self.source = source

        if target is None:
            target = ""
        if action is None:
            action = ""
        if raw is None:
            raw = dict()

        if target != "" or action != "":
            self.target = target
            self.action = action
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
                self.action = raw["action"]
            except KeyError:
                raise EventError("Event data missing 'action' information.")

        self.time = time.time()

    def __repr__(self):
        return "{} - source: {}, target: {},  action: {}".format(time.ctime(self.time),
                                                                 self.source,
                                                                 self.target,
                                                                 self.action)


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


class Game:
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.running = True

        action_thread = threading.Thread(target=self.action_handler, args=tuple())
        action_thread.start()

    def action_handler(self):
        while self.running:
            for a in self.connection_manager.get_actions():
                print(a)


game = Game()
