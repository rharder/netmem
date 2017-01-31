""" A trivial Connector that merely logs outgoing messages. """

import asyncio
import logging

from .connector import Connector

__author__ = "Robert Harder"
__email__ = "rob@iharder.net"
__date__ = "31 Jan 2017"
__license__ = "Public Domain"


class LoggingConnector(Connector):
    """
    Trivial connector that only logs messages as they are sent.
    """

    def __init__(self):
        super().__init__()
        self.log.setLevel(logging.DEBUG)

    def connect(self, listener, loop: asyncio.BaseEventLoop = None):
        super().connect(listener, loop)
        self.log.info("Connected.")
        self.listener.connection_made(self)

    def send_message(self, msg: dict):
        self.log.info("Sending message: {}".format(msg))
