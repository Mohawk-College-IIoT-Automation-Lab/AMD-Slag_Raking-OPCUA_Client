#!/home/daniil/miniconda3/envs/opcua/bin/python
import asyncio
import logging
import time
import random

from asyncua import Client, ua
from asyncua.client.client import Subscription
from asyncua.server import event_generator

URL = "opc.tcp://127.0.0.1:4840"
NAMESPACE = "http://examples.freeopcua.github.io"

class SubHandler(object):
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """
    def __init__(self, client, idx) -> None:
        self.client = client
        self.idx = idx
        self.last_random_value = 0.0

    def datachange_notification(self, node, val, data):
        '''
        The method that is called whenever a data change event occurs in the OPC UA server.
        '''
        asyncio.create_task(self.handle_change(val))

    async def handle_change(self, val):
        print(f"State changed to: {val}")

        if val == "RAKING":
            self.last_random_value = random.uniform(0.0, 100.0)
            print(f"Generated new value: {self.last_random_value:.2f}")

        elif val == "COMPLETE":
            try:
                # Target the steel percentage node
                steel_node = self.client.get_node(ua.NodeId(ua.Int32(11), ua.Int16(self.idx)))
                
                # Write the value
                dv = ua.DataValue(ua.Variant(self.last_random_value, ua.VariantType.Double))
                await steel_node.set_value(dv)
                print(f"Successfully pushed {self.last_random_value:.2f} to server")
            except Exception as e:
                print(f"Failed to write: {e}")


async def main():
    print(f"Connecting to {URL} ...")
    async with Client(url=URL) as client:
        idx = await client.get_namespace_index(NAMESPACE)
        
        handler = SubHandler(client, idx)

        subscription = await client.create_subscription(500, handler)

        state_node = client.get_node(ua.NodeId(ua.Int32(10), ua.Int16(idx)))
        await subscription.subscribe_data_change(state_node)

        print("Subscription active. Waiting for state changes...")
        
        # Keep the connection alive
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())

