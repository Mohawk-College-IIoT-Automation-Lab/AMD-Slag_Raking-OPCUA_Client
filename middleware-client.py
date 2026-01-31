#!/home/daniil/miniconda3/envs/opcua/bin/python
import asyncio
import logging
import time

from asyncua import Client, ua
from asyncua.server import event_generator

URL = "opc.tcp://localhost:4840/freeopcua/server/"
NAMESPACE = "http://examples.freeopcua.github.io"

class SubHandler(object):
    def __init__(self) -> None:
        pass

    def datachange_notification(self, node, val, data):
        '''
        The method that is called whenever a data change event occurs in the OPC UA server.
        '''
        pass


class OPCReader(Client):
    def __init__(self, url, subscription_interval=500):
        super().__init__(url)
        self.subscription_interval = subscription_interval
        self.subscription = None
        self.handler = SubHandler()

    async def __aenter__(self):
        # Call the parent's aenter to handle the actual connection
        await super().__aenter__()
        print(f"Connected to {self.server_url}")
        
        # Auto-setup subscription upon entry
        self.subscription = await self.create_subscription(self.subscription_interval, self.handler)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Cleanup subscription before closing connection
        if self.subscription:
            await self.subscription.delete()
        
        # Call parent's aexit to close the session/transport
        await super().__aexit__(exc_type, exc_val, exc_tb)
        print("Disconnected and cleaned up.")
        

# async def main():
#     print(f"Connecting to {URL} ...")
#     async with Client(url=URL) as client:
#
#         root = client.get_root_node()
#         print(f"Root node is {root}")
#         # Find the namespace index
#         nsidx = await client.get_namespace_index(NAMESPACE)
#         print(f"Namespace Index for '{NAMESPACE}': {nsidx}")
#
#         # Get the stateiable node for read / write
#         line = await client.nodes.objects.get_child(f"{nsidx}:PLine")
#         print(f"PLine node: {line}")
#         state = await client.nodes.root.get_child(f"0:Objects/{nsidx}:PLine/{nsidx}:State")
#         print(f"Node: {state}")
#         print(f"Full value of node: {await state.read_data_value()}")
#         value = await state.read_value()
#         print(f"Value of Speed ({state}): {value}")
#
#         new_value = value - 50
#         print(f"Setting value of Speed to {new_value} ...")
#         await state.write_value(new_value)
#
#         # Calling a method
#         res = await client.nodes.objects.call_method(f"{nsidx}:ServerMethod", 5)
#         print(f"Calling ServerMethod returned {res}")
#
#
# if __name__ == "__main__":
#     asyncio.run(main())

