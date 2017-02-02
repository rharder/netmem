""" Connecting NetworkMemory objects with UDP datagrams. """
import asyncio
import ipaddress
import json
import socket
import struct
import threading

from .connector import Connector, ConnectorListener

__author__ = "Robert Harder"
__email__ = "rob@iharder.net"
__date__ = "20 Jan 2017"
__license__ = "Public Domain"


class UdpConnector(Connector):
    def __init__(self, local_addr: (str, int) = None, remote_addr: (str, int) = None):  # , new_thread: bool = False):
        super().__init__()

        self.local_addr = local_addr or ("225.0.0.1", 9999)
        self.remote_addr = remote_addr or self.local_addr
        # self.new_thread = new_thread

        self.loop = None  # type: asyncio.BaseEventLoop
        self._transport = None  # type: asyncio.DatagramTransport

    def __repr__(self):
        return "{}(local_addr={}, remote_addr={})".format(
            self.__class__.__name__, self.local_addr, self.remote_addr)

    def connect(self, listener: ConnectorListener, netmem_dict, loop: asyncio.BaseEventLoop = None) -> Connector:
        super().connect(listener, netmem_dict, loop=loop)

        async def _connect():
            """ Used internally to connect on the appropriate event loop. """

            # How to make Python listen to multicast
            local_is_multicast = ipaddress.ip_address(self.local_addr[0]).is_multicast
            if local_is_multicast:
                def _make_sock():
                    m_addr, port = self.local_addr
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.bind(('', port))
                    group = socket.inet_aton(m_addr)
                    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                    return sock

                trans, proto = await self.loop.create_datagram_endpoint(lambda: self, sock=_make_sock())
            else:
                # Not multicast
                trans, proto = await self.loop.create_datagram_endpoint(lambda: self, local_addr=self.local_addr)

            assert trans is self._transport
            assert proto is self

        asyncio.run_coroutine_threadsafe(_connect(), loop=self.loop)
        return self

    def close(self):
        self.log.debug("{} : close() called".format(self))
        if self._transport is not None:
            self._transport.close()
            self._transport = None

    def send_message(self, msg: dict):
        self.log.debug("{} : Sending to network: {}".format(self, msg))
        json_data = json.dumps(msg)
        self._transport.sendto(json_data.encode(), self.remote_addr)

    def connection_made(self, transport):
        self.log.info("{} : Connection made {}".format(self, transport))
        self._transport = transport
        self.listener.connection_made(self)

    def connection_lost(self, exc):
        self.log.info("{} : Connection lost (Error: {})".format(self, exc))
        if self._transport is not None:
            self._transport.close()
            self._transport = None
        self.listener.connection_lost(self, exc=exc)

    def datagram_received(self, data, addr):
        self.log.debug("{} : Datagram received from {}: {}".format(self, addr, data))
        msg = json.loads(data.decode())
        self.listener.message_received(self, msg)

    def error_received(self, exc):
        self.log.error("{} : Error received: {}".format(self, exc))
        self.listener.connection_error(self, exc=exc)
