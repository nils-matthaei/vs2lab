"""
Simple client server unit test
"""

import logging
import threading
import unittest
import json
import clientserver
from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)


class TestEchoService(unittest.TestCase):
    """The test"""
    _server = clientserver.Server()  # create single server in class variable
    _server_thread = threading.Thread(target=_server.serve)
    _phone_book = {
            "Alice": "123-456-7890",
            "Bob": "987-654-3210",
            "Charlie": "555-555-5555",
            "David": "444-444-4444",
            "Eve": "333-333-3333"
        }

    @classmethod
    def setUpClass(cls):
        cls._server_thread.start()  # start server loop in a thread (called only once)

    def setUp(self):
        super().setUp()
        self.client = clientserver.Client()  # create new client for each test

    def test_get(self):  # each test_* function is a test
        msg = self.client.get_number("Bob")
        self.assertEqual(msg, '987-654-3210')

    def test_get_wrong_name(self):  # each test_* function is a test
            msg = self.client.get_number("Dr. Christian Pape")
            self.assertEqual(msg, 'Name not found')

    def test_get_all(self):  # each test_* function is a test
        """Test simple call"""
        msg = self.client.get_all_numbers()
        self.assertEqual(msg, json.dumps(self._phone_book))

    def tearDown(self):
        self.client.close()  # terminate client after each test

    @classmethod
    def tearDownClass(cls):
        cls._server._serving = False  # break out of server loop. pylint: disable=protected-access
        cls._server_thread.join()  # wait for server thread to terminate


if __name__ == '__main__':
    unittest.main()
