""" Connecting NetworkMemory objects with pushbullet.com. """

import asyncio
import json
import os
import socket

import aiohttp
from aiohttp import web
from yarl import URL
import asyncpushbullet

from .connector import Connector, ConnectorListener

__author__ = "Robert Harder"
__email__ = "rob@iharder.net"
__date__ = "22 Feb 2017"
__license__ = "Public Domain"


class PushbulletConnector(Connector):
    def __init__(self, api_key: str, device_nickname: str = None, verify_ssl: bool = None):
        super().__init__()

        # Passed parameters
        self._api_key = api_key
        self._device_nickname = device_nickname
        self._verify_ssl = verify_ssl

        # Other Data
        self._account = None  # type: asyncpushbullet.AsyncPushbullet
        self._push_listener = None  # type: asyncpushbullet.PushListener

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, str(self._account))

    def connect(self, listener: ConnectorListener, netmem_dict, loop: asyncio.BaseEventLoop = None) -> Connector:
        super().connect(listener, netmem_dict, loop=loop)

        async def _connect():
            self._account = asyncpushbullet.AsyncPushbullet(api_key=self._api_key, verify_ssl=self._verify_ssl)

            # Wait indefinitely for incoming pushes
            exc = None
            try:
                await self._account.async_verify_key()

                # Need to create a device with given nickname?
                if self._device_nickname is not None:
                    _filter_dev = await self._account.async_get_device(self._device_nickname)
                    if _filter_dev is None:
                        _filter_dev = await self._account.async_new_device(nickname=self._device_nickname)
                        self.log.info("Registered new device with nickname={}: {}".format(self._device_nickname, _filter_dev))
                    else:
                        self.log.info("Found existing device with nickname={}: {}".format(self._device_nickname, _filter_dev))

                # Callback for when it connects
                async def _connected(push_listener):
                    self._push_listener = push_listener
                    self.listener.connection_made(self)  # Must notify NetworkMemory

                async for push in asyncpushbullet.PushListener(self._account,
                                                               on_connect=_connected,
                                                               filter_device_nickname=self._device_nickname):
                    body = push.get("body")
                    try:
                        msg = dict(json.loads(body))
                    except TypeError as e:
                        self.log.error("Invalid push body: not a dict: {}".format(body))
                    else:
                        self.listener.message_received(self, msg)  # notify of incoming update

            except asyncpushbullet.PushbulletError as exc:
                self.log.error(str(exc))
            finally:
                if exc is None:
                    self.listener.connection_lost(self)
                else:
                    self.listener.connection_lost(self, exc)

        asyncio.run_coroutine_threadsafe(_connect(), loop=self.loop)
        return self

    def send_message(self, msg: dict):
        async def _send(json_msg):
            filter_dev = await self._account.async_get_device(self._device_nickname)
            await self._account.async_push_note(title=self.__class__.__name__,
                                                body=json_msg, device=filter_dev)

        asyncio.run_coroutine_threadsafe(_send(json.dumps(msg)), self.loop)

    def close(self):
        self.log.info("{} : Attempting to close pushbullet connection".format(self))

        async def _close():
            self.log.debug("{} : Issuing close commands".format(self))
            await self._push_listener.close()
            await self._account.close()
            # self.listener.connection_lost(self, "closed upon request")

        asyncio.run_coroutine_threadsafe(_close(), self.loop)
