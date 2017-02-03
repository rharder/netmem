"""
NetworkMemory objects are descendents of basic Python dictionaries and can be synchronized
across multiple machines on a network.


Websocket protocol dictionary:

{
    "name" : name of NetworkMemory object
    "changes" :  # List of changes to dictionary
        [
            {
                "key": dictionary key that is changed
                "action": action type - "update", "delete"
                "value": new value, if needed
                "timestamp": unix epoch timestamp of change as a float
            }, ...
        ]

"""
import asyncio
import logging
import threading

from .bindable_variable import BindableDict
from .connector import Connector

__author__ = "Robert Harder"
__email__ = "rob@iharder.net"
__date__ = "2 Feb 2017"
__license__ = "Public Domain"


class NetworkMemory(BindableDict):
    NAME_COUNTER = 1

    def __init__(self, **kwargs):
        if "name" in kwargs:
            self.name = kwargs["name"]
            del kwargs["name"]
        else:
            self.name = "{}_{}".format(self.__class__.__name__, self.NAME_COUNTER)
            self.NAME_COUNTER += 1

        super().__init__(**kwargs)
        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)

        # Data
        self._timestamps = {}  # maps keys to timestamp of change
        self._connectors = []  # type: [Connector]
        self.loop = None  # type: asyncio.BaseEventLoop

    def __repr__(self):
        return "{} {} ({})".format(self.__class__.__name__, self.name, str(self))

    def connect(self, connector: Connector, loop=None):
        return connector.connect(self, self, loop=loop)

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
        self.log.info("{} : Connectors remaining: {}".format(self, len(self._connectors)))
        # connector.close()

    def connection_error(self, connector: Connector, exc=None):
        self.log.warning("{} : Connection error on {}: {}".format(repr(self), connector, exc))
        print("connector_error", connector, exc)

    def message_received(self, connector: Connector, msg: dict):
        self.log.debug("{} : Message received from {}: {}".format(repr(self), connector, msg))

        name = str(msg.get("name"))
        with self:
            for change in msg.get("changes", []):  # type: dict
                timestamp = float(change.get("timestamp", 0))
                action = str(change.get("action", ""))
                if action == "update":
                    if "key" in change:
                        key = str(change["key"])
                        timestamp = float(change.get("timestamp", 0))
                        value = change.get("new_val")
                        self.set(key, value, timestamp=timestamp)
                    else:
                        self.log.error("{} : Received an update with no key specified: {}".format(repr(self), change))

    # End ConnectorListener methods
    # ########

    def _notify_listeners(self):

        if not self._suspend_notifications:
            changes = self._changes.copy()
            if len(changes) > 0:
                data = {"changes": changes, "name": self.name}
                for connector in self._connectors.copy():  # type: Connector
                    self.log.info("{} : Notifying connector {}: {}".format(repr(self), connector, data))
                    connector.send_message(data)

        super()._notify_listeners()

    def close_all(self):
        for connector in self._connectors.copy():  # type: Connector
            connector.close()
