#!/home/daniil/miniconda3/envs/opcua/bin/python
import asyncio
import logging

from asyncua import Server, ua
from asyncua.common.methods import uamethod


@uamethod
def func(parent, value):
    return value * 2


async def main():
    _logger = logging.getLogger(__name__)
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://172.0.0.1:4840")

    # set up our own namespace, not really necessary but should as spec
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # populating our address space
    # server.nodes, contains links to very common nodes like objects and root
    production_line = await server.nodes.objects.add_object(idx,  bname = "PLine", nodeid = "ns=2;i=1",)
    state = await production_line.add_variable(
            nodeid = "ns=2;i=2",
            bname = "State",
            val = 0,
            datatype = int
            )
    
    # Set state to be writable by clients
    await state.set_writable()
    await server.nodes.objects.add_method(
        ua.NodeId("ServerMethod", idx),
        ua.QualifiedName("ServerMethod", idx),
        func,
        [ua.VariantType.Int64],
        [ua.VariantType.Int64],
    )
    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(1)
            _logger.info(f"Current State: {state}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main(), debug=True)
