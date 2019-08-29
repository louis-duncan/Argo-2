import socket
import threading
import time

import requests
import json
from _globals import *


class Communicator:
    def __init__(self):
        self.current_state = None
        self.connection = socket.create_connection((ADDRESS, SEND_PORT))
        self.action_queue = []

        self._grab_thread = threading.Thread(target=self._grab_loop,
                                             args=((ADDRESS, GET_PORT),))
        self._send_thread = threading.Thread(target=self._action_sender)

        self.run = True
        self._grab_thread.start()
        self._send_thread.start()

    def _grab_loop(self, address):
        to_min = 0.2
        to_max = 10
        time_out = to_min
        while self.run:
            r = requests.get("http://{}:{}/game_state.json".format(*address))
            if r.status_code != 200:
                time_out = time_out * 2 if time_out <= to_max * 2 else to_max
            else:
                time_out = to_min
                self.current_state = json.loads(r.text)
            time.sleep(time_out)

    def _action_sender(self):
        time_out = 0.1
        while self.run:
            while len(self.action_queue) > 0:
                self._send_action(self.action_queue.pop(0))
                if len(self.action_queue) == 0:
                    break
                time.sleep(time_out)
            else:
                time.sleep(time_out)

    def _send_action(self, action):
        text = json.dumps(action)
        len_bytes = bytes([len(text) // 256, len(text) % 256])
        self.connection.send(len_bytes)
        self.connection.send(text.encode())

    def still_running(self):
        return self._grab_thread.is_alive() and self._send_thread.is_alive()

