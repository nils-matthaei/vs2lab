"""
Client and server using classes
"""

import logging
import socket
import json
import const_cs
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)  # init loging channels for the lab

# pylint: disable=logging-not-lazy, line-too-long

class Server:
    """ The server """
    _logger = logging.getLogger("vs2lab.lab1.clientserver.Server")
    _serving = True

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # prevents errors due to "addresses in use"
        self.sock.bind((const_cs.HOST, const_cs.PORT))
        self.sock.settimeout(3)  # time out in order not to block forever
        self._logger.info("Server bound to socket: %s", str(self.sock))

        self.phone_book = {
            "Alice": "123-456-7890",
            "Bob": "987-654-3210",
            "Charlie": "555-555-5555",
            "David": "444-444-4444",
            "Eve": "333-333-3333"
        }

    def serve(self):
        """ Serve echo """
        self.sock.listen(1)
        self._logger.info("Server is listening for connections.")

        while self._serving:  # as long as _serving (checked after connections or socket timeouts)
            try:
                self._logger.info("Waiting for a connection...")
                (connection, address) = self.sock.accept()  # returns new socket and address of client
                self._logger.info("Connection accepted from: %s", str(address))

                while True:  # forever
                    data = connection.recv(1024)  # receive data from client
                    if not data:
                        self._logger.info("No data received. Closing connection to: %s", str(address))
                        break  # stop if client stopped

                    message = data.decode('ascii').strip()
                    self._logger.info("Received message: %s", message)
                    parts = message.split()

                    action = parts[0]
                    response = ''
                    if action == 'GET':
                        response = self.get(parts[1]) if len(parts) >= 2 else "No name supplied"
                    elif action == 'GETALL':
                        response = json.dumps(self.get_all())
                    else:
                        response = 'Action not supported'

                    self._logger.info("Sending response: %s", response)
                    connection.send(response.encode('ascii'))  # return phone number of your tinder date

                connection.close()  # close the connection
                self._logger.info("Connection closed for: %s", str(address))
            except socket.timeout:
                self._logger.info("Socket timeout occurred, continuing to listen.")
                pass  # ignore timeouts

        self.sock.close()
        self._logger.info("Server down.")


    def get(self, name):
        return self.phone_book.get(name, "Name not found")

    def get_all(self):
        return self.phone_book


class Client:
    """ The client """
    logger = logging.getLogger("vs2lab.a1_layers.clientserver.Client")

    def call(self, msg_in):
        """ Call server """
        self.logger.info("Creating socket.")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger.info("Socket created: %s", str(self.sock))

        self.logger.info("Connecting to server at %s:%d", const_cs.HOST, const_cs.PORT)
        self.sock.connect((const_cs.HOST, const_cs.PORT))
        self.logger.info("Client connected to socket: %s", str(self.sock))

        self.logger.info("Sending message: %s", msg_in)
        self.sock.send(msg_in.encode('ascii'))  # send encoded string as data
        self.logger.info("Message sent, waiting for response.")

        data = self.sock.recv(1024)  # receive the response
        msg_out = data.decode('ascii')
        self.logger.info("Received response: %s", msg_out)  # log the received result

        self.sock.close()  # close the connection
        self.logger.info("Socket closed. Client down.")

        return msg_out

    def get_number(self, name):
        # check inputs for validity
        if name == "":
            print("Please provide a name")
        # networking harder than the average linkedin user
        message = "GET " + name
        return self.call(message)

    def get_all_numbers(self):
        # networking harder than the average linkedin user
        message = "GETALL"
        return self.call(message)


    def close(self):
        """ Close socket """
        self.sock.close()
