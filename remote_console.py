import json
import socket
import _globals
import os


def clear_screen():
    os.system("cls")


addr = input("Enter Address (<ENTER> for 'localhost'): ")
if addr == "":
    addr = "localhost"
port = input("Enter Port No. (<ENTER> for '1234'): ")
if port == "":
    port = 1234
else:
    port = int(port)

con = socket.create_connection((addr, port))

while True:
    command = input("}}} ").lower()

    if command == "exit":
        exit(0)
    elif command == "recon":
        con = socket.create_connection((addr, port))
        continue
    else:
        pass

    command_parts = command.split(" ")

    if len(command_parts) < 2:
        print("Invalid command syntax. Should be '<command> <target> <args>'.\n")
        continue
    else:
        action = command_parts[0]
        target = command_parts[1]
        args = command_parts[2:]

    if not (action in _globals.SERVER_COMMANDS.keys()):
        print("Unknown command '{}'\n".format(action))
    elif action != "send_msg" and len(args) != len(_globals.SERVER_COMMANDS[action]):
        print("Expected {} arguments for command '{}', but got {}.\n"
              "Syntax should be '<command> <target> <args>'\n"
              "Expected args for '{}' should be:\n"
              "{}\n".format(len(_globals.SERVER_COMMANDS[action]),
                            action,
                            len(args),
                            action,
                            " ".join(_globals.SERVER_COMMANDS[action])))
    elif action == "send_msg" and len(args) > 0:
        to_send = {"target": target,
                   "action": action,
                   "args": [" ".join(args)]}
        con.send((json.dumps(to_send) + "\n").encode())
    elif action == "send_msg" and len(args) == 0:
        print("Command send_msg required a message.\n")
    else:
        to_send = {"target": target,
                   "action": action,
                   "args": args}
        con.send((json.dumps(to_send) + "\n").encode())
