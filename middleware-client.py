#!/home/daniil/miniconda3/envs/opcua/bin/python
import asyncio
import logging
import time

from asyncua import Client, ua
from asyncua.server import event_generator

URL = "opc.tcp://127.0.0.1:4840"
NAMESPACE = "http://examples.freeopcua.github.io"

class SubHandler(object):
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """
    def __init__(self) -> None:
        pass

    def datachange_notification(self, node, val, data):
        '''
        The method that is called whenever a data change event occurs in the OPC UA server.
        '''
        print("Current state:", val)
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
        

async def main():
    print(f"Connecting to {URL} ...")
    async with Client(url=URL) as client:
        idx = await client.get_namespace_index(NAMESPACE)
        state = client.get_node(ua.NodeId(ua.Int32(10), ua.Int16(idx)))

        # Create subscription hander
        handler = SubHandler()

        # Create subscription
        subscription = await client.create_subscription(500, handler)

        # Subscribe to data changes on the state variable node
        await subscription.subscribe_data_change(state)

        # We let the subscription run for ten seconds
        await asyncio.sleep(10)
        # We delete the subscription (this un-subscribes from the data changes of the two variables).
        # This is optional since closing the connection will also delete all subscriptions.
        await subscription.delete()
        # After one second we exit the Client context manager - this will close the connection.
        await asyncio.sleep(1)



if __name__ == "__main__":
    asyncio.run(main())

