""" Connecting NetworkMemory objects with http websockets. """

import asyncio

import aiohttp
from aiohttp import web
from yarl import URL

from .connector import Connector, ConnectorListener

__author__ = "Robert Harder"
__email__ = "rob@iharder.net"
__date__ = "20 Jan 2017"
__license__ = "Public Domain"


class WsServerConnector(Connector):
    def __init__(self, host="127.0.0.1", port=8080, ssl_context=None):
        super().__init__()

        self.host = host
        self.port = port
        self.ssl_context = ssl_context

        self.app = None  # type: web.Application
        self.handler = None  # type: web.Server
        self.srv = None  # type: asyncio.base_events.Server
        self.active_sockets = []  # type: [web.WebSocketResponse]

        scheme = 'https' if self.ssl_context else 'http'
        url = URL('{}://localhost'.format(scheme))
        self.url = url.with_host(self.host).with_port(self.port)

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.url)

    def connect(self, listener: ConnectorListener, loop=None) -> Connector:
        super().connect(listener, loop)

        async def _connect():
            self.app = web.Application(loop=self.loop)
            self.app.router.add_get("/", self.websocket_handler)
            await self.app.startup()
            self.handler = self.app.make_handler()
            self.srv = await self.loop.create_server(self.handler, host=self.host,
                                                     port=self.port, ssl=self.ssl_context)
            self.log.info("{} : Websocket server listening".format(self))
            self.listener.connection_made(self)  # Must notify NetworkMemory

        asyncio.run_coroutine_threadsafe(_connect(), loop=self.loop)
        return self

    def send_message(self, msg: dict):
        self.log.debug("{} : Sending update to {} connected clients".format(self, len(self.active_sockets)))
        for ws in self.active_sockets.copy():
            ws.send_json(msg)

    def close(self):
        self.log.info("{} : Attempting to close websocket server".format(self))

        async def _close():
            self.log.debug("{} : Issuing close commands".format(self))
            self.srv.close()
            await self.srv.wait_closed()
            await self.app.shutdown()
            await self.handler.shutdown()
            await self.app.cleanup()
            self.listener.connection_lost(self, "closed upon request")

        asyncio.run_coroutine_threadsafe(_close(), self.loop)

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.active_sockets.append(ws)
        self.log.info("{} : Client connected to websocket {}".format(self, ws))

        exc = None
        try:
            async for msg in ws:  # type: aiohttp.WSMessage
                if msg.type == aiohttp.WSMsgType.TEXT:
                    self.listener.message_received(self, msg.json())

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.log.error("{} : Websocket connection error: {}".format(self, ws.exception()))
                    self.listener.connection_error(self, ws.exception())
                    exc = ws.exception()

        except Exception as e:
            self.log.error("{} : Websocket connection error: {}".format(self, e))
            self.listener.connection_error(self, e)
            exc = e
        finally:
            self.log.info("{} : Client disconnected from websocket connection {}".format(self, ws))
            self.active_sockets.remove(ws)
            self.listener.connection_lost(self, exc)
        return ws


class WsClientConnector(Connector):
    def __init__(self, url: str = None):
        super().__init__()
        self.url = url
        self.loop = None  # type: asyncio.BaseEventLoop
        self.session = None  # type: aiohttp.ClientSession
        self.ws = None  # type: aiohttp.ClientWebSocketResponse

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.url)

    def connect(self, listener: ConnectorListener, loop=None) -> Connector:
        super().connect(listener, loop)
        asyncio.run_coroutine_threadsafe(self._connect(), loop=self.loop)
        return self

    async def _connect(self):
        self.session = aiohttp.ClientSession()
        async with self.session.ws_connect(self.url) as ws:  # type: aiohttp.ClientWebSocketResponse
            self.ws = ws
            self.log.info("{} : Websocket client connected {}".format(self, ws))
            self.listener.connection_made(self)  # Must register with NetworkMemory

            exc = None
            try:
                async for msg in ws:  # type: aiohttp.WSMessage
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        self.listener.message_received(self, msg.json())

                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        self.log.error("Websocket connection error: {}".format(ws.exception()))
                        self.listener.connection_error(self, ws.exception())

            except Exception as e:
                self.log.error("{} : Websocket connection error: {}".format(self, e))
                self.listener.connection_error(self, e)
                exc = e
            finally:
                self.log.info("{} : Client disconnected from websocket connection {}".format(self, ws))
                self.listener.connection_lost(self, exc)
        self.log.info("{} websocket client closed: {}".format(self, ws))
        self.listener.connection_lost(self, "connection closed")
        self.ws = None

    def send_message(self, msg: dict):
        self.log.debug("Sending message to websocket server {}".format(self.ws))
        self.ws.send_json(msg)

    def close(self):
        self.loop.call_soon_threadsafe(self.ws.close)
