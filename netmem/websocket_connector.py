""" Connecting NetworkMemory objects with http websockets. """

import asyncio
import os
import socket

import aiohttp
from aiohttp import web
from yarl import URL

from netmem.websocket_server import WsServer
from .connector import Connector, ConnectorListener

__author__ = "Robert Harder"
__email__ = "rob@iharder.net"
__date__ = "2 Feb 2017"
__license__ = "Public Domain"


class WsServerConnector(Connector):
    WS_UPDATES = "/ws_updates"
    WS_WHOLE = "/ws_whole"
    HTML_VIEW = "/"

    def __init__(self, host="0.0.0.0", port=8080, ssl_context=None):
        super().__init__()

        self.host = host
        self.port = port
        self.ssl_context = ssl_context

        self._app = None  # type: web.Application
        self._handler = None  # type: web.Server
        self._srv = None  # type: asyncio.base_events.Server

        # Websocket server to handle updates to netmem
        self._ws_server_updates = WsServer()  # type: WsServer
        self._ws_server_updates.on_message = self.on_update_message

        # Websocket server to handle complete echoing of entire netmem contents
        self._ws_server_whole = WsServer()  # type: WsServer
        self._ws_server_whole.on_websocket = self.on_whole_websocket

        ht_scheme = 'https' if self.ssl_context else 'http'
        ws_scheme = 'wss' if self.ssl_context else 'ws'
        ht_url = URL('{}://localhost'.format(ht_scheme))
        ws_url = URL('{}://localhost'.format(ws_scheme))
        self.ht_url_base = ht_url.with_host(socket.gethostname()).with_port(self.port)
        self.ws_url_base = ws_url.with_host(socket.gethostname()).with_port(self.port)

        # self.url_ws_updates = self.ws_url_base.join(URL(WsServerConnector.WS_UPDATES))  # Doesn't join right
        # self.url_ws_whole = self.ws_url_base.join(URL(WsServerConnector.WS_WHOLE))
        self.url_ws_updates = URL(str(self.ws_url_base) + WsServerConnector.WS_UPDATES)
        self.url_ws_whole = URL(str(self.ws_url_base) + WsServerConnector.WS_WHOLE)

        self.url_html_view = self.ht_url_base.join(URL(WsServerConnector.HTML_VIEW))

        self.log.info("{} : Hosting html view at {}".format(self, self.url_html_view))
        self.log.info("{} : Hosting websocket memory updates at {}".format(self, self.url_ws_updates))
        self.log.info("{} : Hosting websocket memory complete reflection at {}".format(self, self.url_ws_whole))

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.ht_url_base)

    def connect(self, listener: ConnectorListener, netmem_dict, loop: asyncio.BaseEventLoop = None) -> Connector:
        super().connect(listener, netmem_dict, loop=loop)

        async def _connect():
            self._app = web.Application(loop=self.loop)

            self._app.router.add_get(WsServerConnector.WS_UPDATES, self._ws_server_updates.websocket_handler)
            self._app.router.add_get(WsServerConnector.WS_WHOLE, self._ws_server_whole.websocket_handler)

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
        self._ws_server_updates.broadcast_json(msg)  # update
        self._ws_server_whole.broadcast_json(self.netmem)  # entire contents

    def close(self):
        self.log.info("{} : Attempting to close websocket server".format(self))

        async def _close():
            self.log.debug("{} : Issuing close commands".format(self))
            self._srv.close()
            await self._srv.wait_closed()

            await self._ws_server_updates.close_websockets()
            await self._ws_server_whole.close_websockets()

            await self._app.shutdown()
            await self._app.cleanup()
            self.listener.connection_lost(self, "closed upon request")

        asyncio.run_coroutine_threadsafe(_close(), self.loop)

    async def on_update_message(self, ws: web.WebSocketResponse, ws_msg_from_client: aiohttp.WSMessage):
        if ws_msg_from_client.type == aiohttp.WSMsgType.TEXT:
            self.listener.message_received(self, ws_msg_from_client.json())

    async def on_whole_websocket(self, ws: web.WebSocketResponse):
        ws.send_json(self.netmem)  # Send initial copy of entire netmem
        async for ws_msg in ws:  # type: aiohttp.WSMessage
            await self.on_whole_message(ws=ws, ws_msg_from_client=ws_msg)

    async def on_whole_message(self, ws: web.WebSocketResponse, ws_msg_from_client: aiohttp.WSMessage):
        if ws_msg_from_client.type == aiohttp.WSMsgType.TEXT:
            ws.send_json(self.netmem)  # Simply echo back complete contents whenever pinged

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

    def connect(self, listener: ConnectorListener, netmem_dict, loop: asyncio.BaseEventLoop = None) -> Connector:
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
                            self.log.error(
                                "{} : Websocket {} connection error: {}".format(self, id(ws), ws.exception()))
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
