#!/home/daniil/miniconda3/envs/opcua/bin/python
import asyncio
import logging

from asyncua import Server, ua
from asyncua.common.methods import uamethod




async def main():
    _logger = logging.getLogger(__name__)
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://127.0.0.1:4840")

    # set up our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    production_line = await server.nodes.objects.add_object(nodeid="ns=2;i=1",
                                                            bname = "PLine",)
    state = await production_line.add_variable(
            nodeid="ns=2;i=10",
            bname = "State",
            val = "IDLE",
            )
    
    # Set state to be writable by clients
    await state.set_writable()
    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(1)
            value = await state.read_value()
            _logger.info(f"Current State: {value}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(), debug=True)
