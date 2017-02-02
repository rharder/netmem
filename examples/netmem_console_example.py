#!/usr/bin/env python3
import asyncio
import logging

import sys

import netmem

__author__ = "Robert Harder"
__email__ = "rob@iharder.net"
__date__ = "31 Jan 2017"
__license__ = "Public Domain"

# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger(__name__).setLevel(logging.DEBUG)


def main():
    example_NetworkMemory()


def example_NetworkMemory():
    loop = asyncio.get_event_loop()

    mem1 = netmem.NetworkMemory()
    mem2 = netmem.NetworkMemory()
    mem3 = netmem.NetworkMemory()

    def _when_mem1_changes(var: netmem.NetworkMemory, name, old_val, new_val):
        print("mem1 '{}' changed from {} to {}: {}".format(name, old_val, new_val, str(var)))

    def _when_mem2_changes(var: netmem.NetworkMemory, name, old_val, new_val):
        print("mem2 '{}' changed from {} to {}: {}".format(name, old_val, new_val, str(var)))

    def _when_mem3_changes(var: netmem.NetworkMemory, name, old_val, new_val):
        print("mem3 '{}' changed from {} to {}: {}".format(name, old_val, new_val, str(var)))

    mem1.add_listener(_when_mem1_changes)
    mem2.add_listener(_when_mem2_changes)
    mem3.add_listener(_when_mem3_changes)

    # Connect just mem1 and mem2 together using multicast on local machines
    # : Uncomment below to try it
    mem1.connect(netmem.UdpConnector(local_addr=("225.0.0.1", 9991), remote_addr=("225.0.0.2", 9992)))
    mem2.connect(netmem.UdpConnector(local_addr=("225.0.0.2", 9992), remote_addr=("225.0.0.1", 9991)))

    # The LoggingConnector simply logs changes to the memory.  It does not listen for changes from anything.
    # : Uncomment below to try it
    mem1.connect(netmem.LoggingConnector())

    # Connect three together with websockets, one acting as the server and the other as clients.
    # The websocket connectors support two-way communication, so even though one is hosting the
    # http server, all three with be notified of changes to each other.
    # : Uncomment below to try it
    # wss = mem1.connect(netmem.WsServerConnector(port=8080))
    # mem2.connect(netmem.WsClientConnector(url=wss.url_ws_updates))
    # mem3.connect(netmem.WsClientConnector(url=wss.url_ws_updates))

    async def prompt():
        await asyncio.sleep(1)
        while True:
            key = input("Key? ")
            if key == "":
                await asyncio.sleep(0.5)
                continue
            value = input("Value? ")
            mem1.set(key, value)
            await asyncio.sleep(0.5)  # Because input() locks up the event loop, when need to yield some time

    asyncio.ensure_future(prompt())

    try:
        print("Starting loop...")
        loop.run_forever()
    except KeyboardInterrupt:
        sys.exit(1)
    loop.close()


if __name__ == "__main__":
    main()
