""" Connecting NetworkMemory objects with http websockets. """

import asyncio
import os
import socket

import aiohttp
from aiohttp import web
from yarl import URL

from .connector import Connector, ConnectorListener

__author__ = "Robert Harder"
__email__ = "rob@iharder.net"
__date__ = "2 Feb 2017"
__license__ = "Public Domain"


class WsServerConnector(Connector):
    WS_UPDATES = "/ws_updates"
    WS_WHOLE = "/ws_whole"
    HTML_VIEW = "/"

    def __init__(self, host="0.0.0.0", port=8080, ssl_context=None, netmem_dict:dict=None):
        super().__init__()

        self.host = host
        self.port = port
        self.ssl_context = ssl_context
        self.netmem = netmem_dict  # Reference to the hosting networkmemory

        self._app = None  # type: web.Application
        self._handler = None  # type: web.Server
        self._srv = None  # type: asyncio.base_events.Server
        self._active_ws_updates_sockets = []  # type: [web.WebSocketResponse]
        self._active_ws_whole_sockets = []  # type: [web.WebSocketResponse]

        scheme = 'https' if self.ssl_context else 'http'
        url = URL('{}://localhost'.format(scheme))
        self.url_base = url.with_host(socket.gethostname()).with_port(self.port)

        self.url_ws_updates = self.url_base.join(URL(WsServerConnector.WS_UPDATES))
        self.url_ws_whole = self.url_base.join(URL(WsServerConnector.WS_WHOLE))
        self.url_html_view = self.url_base.join(URL(WsServerConnector.HTML_VIEW))

        self.log.info("{} : Hosting html view at {}".format(self, self.url_html_view))
        self.log.info("{} : Hosting websocket memory updates at {}".format(self, self.url_ws_updates))
        self.log.info("{} : Hosting websocket memory complete reflection at {}".format(self, self.url_ws_whole))

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.url_base)

    def connect(self, listener: ConnectorListener, netmem_dict, loop: asyncio.BaseEventLoop=None) -> Connector:
        super().connect(listener, netmem_dict, loop=loop)

        async def _connect():
            self._app = web.Application(loop=self.loop)
            self._app.router.add_get(WsServerConnector.WS_UPDATES, self.ws_updates_handler)
            self._app.router.add_get(WsServerConnector.WS_WHOLE, self.ws_whole_handler)
            self._app.router.add_get(WsServerConnector.HTML_VIEW, self.html_view_handler)

            # Provide an HTML page showing activity?
            # self.log.info("{} : Serving html view at {}".format(self, self.url_html_view))

            await self._app.startup()
            self._handler = self._app.make_handler()
            self._srv = await self.loop.create_server(self._handler, host=self.host,
                                                      port=self.port, ssl=self.ssl_context)
            self.log.info("{} : Websocket server listening".format(self))
            self.listener.connection_made(self)  # Must notify NetworkMemory

        asyncio.run_coroutine_threadsafe(_connect(), loop=self.loop)
        return self

    def send_message(self, msg: dict):
        self.log.debug("{} : Sending update to {} connected clients".format(self, len(self._active_ws_updates_sockets)))
        for ws in self._active_ws_updates_sockets.copy():  # type: web.WebSocketResponse
            ws.send_json(msg)

        if self.netmem is not None:
            for ws in self._active_ws_whole_sockets.copy():  # type: web.WebSocketResponse
                ws.send_json(self.netmem)

    def close(self):
        self.log.info("{} : Attempting to close websocket server".format(self))

        async def _close():
            self.log.debug("{} : Issuing close commands".format(self))
            self._srv.close()
            await self._srv.wait_closed()
            await self._app.shutdown()
            await self._handler.shutdown()
            await self._app.cleanup()
            self.listener.connection_lost(self, "closed upon request")

        asyncio.run_coroutine_threadsafe(_close(), self.loop)

    async def ws_updates_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._active_ws_updates_sockets.append(ws)
        self.log.info("{} : Incoming client connected to websocket {}".format(self, id(ws)))

        exc = None
        try:
            async for msg in ws:  # type: aiohttp.WSMessage
                if msg.type == aiohttp.WSMsgType.TEXT:
                    self.listener.message_received(self, msg.json())

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.log.error("{} : Websocket {} connection error: {}".format(self, id(ws), ws.exception()))
                    self.listener.connection_error(self, ws.exception())
                    exc = ws.exception()
                    self.close()

        except Exception as e:
            self.log.error("{} : Websocket {} connection error: {}".format(self, id(ws), e))
            self.listener.connection_error(self, e)
            exc = e
        finally:
            self.log.info("{} : Client disconnected from websocket connection {}".format(self, id(ws)))
            ws.close()
            self._active_ws_updates_sockets.remove(ws)
        return ws

    async def ws_whole_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._active_ws_whole_sockets.append(ws)
        self.log.info("{} : Incoming client connected to websocket {}".format(self, id(ws)))

        exc = None
        try:
            if self.netmem is not None:
                ws.send_json(self.netmem)

            async for msg in ws:  # type: aiohttp.WSMessage
                if msg.type == aiohttp.WSMsgType.TEXT:
                    self.listener.message_received(self, msg.json())
                    self.log.info("{} : Unexpected incoming message to ws_whole_handler: {}".format(self, msg.data))

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    self.log.error("{} : Websocket {} connection error: {}".format(self, id(ws), ws.exception()))
                    self.listener.connection_error(self, ws.exception())
                    exc = ws.exception()
                    self.close()

        except Exception as e:
            self.log.error("{} : Websocket {} connection error: {}".format(self, id(ws), e))
            self.listener.connection_error(self, e)
            exc = e
        finally:
            self.log.info("{} : Client disconnected from websocket connection {}".format(self, id(ws)))
            ws.close()
            self._active_ws_whole_sockets.remove(ws)
        return ws

    async def html_view_handler(self, request):
        dir = os.path.dirname(__file__)
        html_dir = os.path.abspath(os.path.join(dir, "html"))
        html_view_filename = os.path.join(html_dir, "html_view.html")
        with open(html_view_filename) as f:
            html_data = f.read()
        return web.Response(text=html_data, content_type="text/html")


class WsClientConnector(Connector):
    def __init__(self, url: str = None):
        super().__init__()
        self.url = url
        self.loop = None  # type: asyncio.BaseEventLoop
        self.session = None  # type: aiohttp.ClientSession
        self.ws = None  # type: aiohttp.ClientWebSocketResponse

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.url)

    def connect(self, listener: ConnectorListener, netmem_dict, loop: asyncio.BaseEventLoop=None) -> Connector:
        super().connect(listener, netmem_dict, loop=loop)

        async def _connect():
            self.session = aiohttp.ClientSession(loop=self.loop)
            async with self.session.ws_connect(self.url) as ws:  # type: aiohttp.ClientWebSocketResponse
                self.ws = ws
                self.log.info("{} : Websocket client connected {}".format(self, id(ws)))
                self.listener.connection_made(self)  # Must register with NetworkMemory

                exc = None
                try:
                    async for msg in ws:  # type: aiohttp.WSMessage
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            self.listener.message_received(self, msg.json())

                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            self.log.error("{} : Websocket {} connection error: {}".format(self, id(ws), ws.exception()))
                            self.listener.connection_error(self, ws.exception())

                except Exception as e:
                    self.log.error("{} : Websocket {} connection error: {}".format(self, id(ws), e))
                    self.listener.connection_error(self, e)
                    exc = e
                finally:
                    self.log.info("{} : Client disconnected from websocket {}".format(self, id(ws)))
                    self.listener.connection_lost(self, exc)
            self.log.info("{} : Websocket client closed {}".format(self, id(ws)))
            self.listener.connection_lost(self, "connection closed")
            self.ws = None

        asyncio.run_coroutine_threadsafe(_connect(), loop=self.loop)
        return self


    def send_message(self, msg: dict):
        self.log.debug("Sending message to server on websocket {}".format(id(self.ws)))
        self.ws.send_json(msg)

    def close(self):
        self.loop.call_soon_threadsafe(self.ws.close)
