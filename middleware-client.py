#!/home/daniil/miniconda3/envs/opcua/bin/python
import asyncio
import logging
import time
import json
import random
import queue
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from asyncua import Client, ua
from asyncua.client.client import Subscription
from asyncua.server import event_generator

SERVER_IP = "127.0.0.1"
URL = f"opc.tcp://{SERVER_IP}:49320/FTLinxGateway/"
NAMESPACE = "http://examples.freeopcua.github.io"

BROKER = "localhost"
PORT = 1883
EVENT_TOPIC = "test/events"
DATA_TOPIC = "test/data"
data_queue = queue.Queue()


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connection to MQTT Server Successful")

        # TODO: change QoS to an appropriate level
        client.subscribe(DATA_TOPIC, qos=0)
    else:
        print(f"Connection failed: {reason_code.getName()}")

def on_message(client, usedata, message, properties=None):
    # TOOO: unpack json
    # TODO: write data to opcua
    decoded_message = message.payload.decode('utf-8')
    data = json.loads(decoded_message)
    data_queue.put(data)
    print(f':Simulating writing {data["steel_pct"]} to the OPC UA server')

class SubHandler(object):
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """
    def __init__(self, client, idx, mqttc: mqtt.Client) -> None:
        self.client = client
        self.idx = idx
        self.last_random_value = 0.0
        self.mqttc = mqttc

    def datachange_notification(self, node, val, data):
        '''
        The method that is called whenever a data change event occurs in the OPC UA server.
        '''
        asyncio.create_task(self.handle_change(val))

    async def handle_change(self, val):
        print(f"State changed to: {val}")

        if val == "RAKING":
            # Publish to raking event topic that the raking has started and is in process
            # TODO: change QoS to an appropriate level
            self.mqttc.publish(EVENT_TOPIC, 1)

        elif val == "COMPLETE":
            # Publish to raking event topic that the raking has completed
            # TODO: change QoS to an appropriate level
            self.mqttc.publish(EVENT_TOPIC, 0)
                                    


async def main():
    # Creating mqtt_client instance
    mqtt_client = mqtt.Client(CallbackAPIVersion.VERSION2)

    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    mqtt_client.connect(BROKER, PORT)

    try:
        mqtt_client.loop_start()

        print(f"Connecting to {URL} ...")
        async with Client(url=URL) as client:
            idx = await client.get_namespace_index(NAMESPACE)

            handler = SubHandler(client, idx, mqtt_client)

            subscription = await client.create_subscription(500, handler)

            state_node = client.get_node(ua.NodeId(ua.Int32(10), ua.Int16(idx)))
            await subscription.subscribe_data_change(state_node)

            print("Subscription active. Waiting for state changes...")

            # Target the steel percentage node
            steel_node = client.get_node(ua.NodeId(ua.Int32(11), ua.Int16(idx)))
            
            # Keep the connection alive
            while True:
                try:
                    # Get value from mqtt
                    try:
                        raking_data = data_queue.get(block=False)
                        steel_pct = raking_data["steel_pct"]
                    except queue.Empty:
                        await asyncio.sleep(1)
                        continue
                    # Write the value
                    dv = ua.DataValue(ua.Variant(steel_pct, ua.VariantType.Double))
                    await steel_node.set_value(dv)
                    print(f"Successfully pushed {steel_pct} to server")
                except Exception as e:
                    print(f"Failed to write: {e}")
                await asyncio.sleep(1)
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

