"""
NetworkMemory objects are descendents of basic Python dictionaries and can be synchronized
across multiple machines on a network.
"""
import asyncio
import logging
import socket
import threading
import time

from .bindable_variable import BindableDict
from .connector import Connector

__author__ = "Robert Harder"
__email__ = "rob@iharder.net"
__date__ = "20 Jan 2017"
__license__ = "Public Domain"


class NetworkMemory(BindableDict):
    def __init__(self, **kwargs):
        if "name" in kwargs:
            self.name = kwargs["name"]
            del kwargs["name"]
        else:
            self.name = socket.gethostname()

        super().__init__(**kwargs)
        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)

        # Data
        self._timestamps = {}  # maps keys to timestamp of change
        self._connectors = []  # type: [Connector]
        self.loop = None  # type: asyncio.BaseEventLoop

    def __repr__(self):
        return "{} {} ({})".format(self.__class__.__name__, self.name, str(self))

    def connect(self, connector: Connector, loop=None):
        return connector.connect(self, loop=loop)

    def connect_on_new_thread(self, connector):
        ioloop = asyncio.new_event_loop()
        c = self.connect(connector, loop=ioloop)
        t = threading.Thread(target=lambda: ioloop.run_forever())
        t.daemon = True
        t.start()
        return c

    # ########
    # ConnectorListener methods

    def connection_made(self, connector: Connector):
        self.log.info("{} : Connection made {}".format(repr(self), connector))
        self._connectors.append(connector)
        connector.message_received = self.message_received

    def connection_lost(self, connector: Connector, exc=None):
        self.log.info("{} : Connection lost. Removing {} ({})".format(repr(self), connector, exc))
        self._connectors.remove(connector)

    def connection_error(self, connector: Connector, exc=None):
        self.log.warning("{} : Connection error on {}: {}".format(repr(self), connector, exc))
        print("connector_error", connector, exc)

    def message_received(self, connector: Connector, msg: dict):
        self.log.debug("{} : Message received from {}: {}".format(repr(self), connector, msg))

        if "update" in msg:
            changes = msg["update"]
            host = str(msg.get("host"))
            timestamp = float(msg.get("timestamp"))
            updates = {}

            for key, old_val, new_val in changes:
                if timestamp > self._timestamps.get(key, 0):
                    self.log.debug("{} : Received fresh network data from {}: {} = {}"
                                   .format(repr(self), host, key, new_val))
                    updates[key] = new_val
                    self._timestamps[key] = timestamp
                else:
                    self.log.debug("{} : Received stale network data from {}: {} = {}"
                                   .format(repr(self), host, key, new_val))

            self.update(updates)

    # End ConnectorListener methods
    # ########

    def _notify_listeners(self):

        if not self._suspend_notifications:
            changes = self._changes.copy()
            timestamp = time.time()
            if len(changes) > 0:
                data = {"update": changes, "timestamp": timestamp, "host": self.name}
                for connector in self._connectors.copy():  # type: Connector
                    # connector.loop.call_soon(connector.send_message, data)
                    self.log.info("{} : Notifying connector {}".format(repr(self), connector))
                    connector.send_message(data)

        super()._notify_listeners()

    def close_all(self):
        for connector in self._connectors.copy():  # type: Connector
            connector.close()
