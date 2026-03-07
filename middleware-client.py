#!/home/daniil/miniconda3/envs/opcua/bin/python
import asyncio
import logging
import time
import json
import queue
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from asyncua import Client, ua
from asyncua.client.client import Subscription
from asyncua.server import event_generator

HOSTNAME = "iiot-daniil"
URL = f"opc.tcp://{HOSTNAME}:4990/FactoryTalkLinxGateway/"
NAMESPACE = 2

LADLE_TILT_STATE_INDEX = 0 
RAKE_HOME_STATE_INDEX = 1
HEAT_ID_INDEX = 0
TIME_INDEX = 1
PULLS_INDEX = 2

BROKER = "localhost"
PORT = 1883
EVENT_TOPIC = "raking/events"
DATA_TOPIC = "raking/data"
TEMPERATURE_TOPIC = "raking/camera_temperature"
data_queue = queue.Queue()


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connection to MQTT Server Successful")

        # TODO: change QoS to an appropriate level
        client.subscribe(DATA_TOPIC, qos=2)
    else:
        print(f"Connection failed: {reason_code.getName()}")

def on_message(client, usedata, message, properties=None):
    # TOOO: unpack json
    # TODO: write data to opcua
    decoded_message = message.payload.decode('utf-8')
    data = json.loads(decoded_message)
    data_queue.put(data)
    print(f':Simulating writing {data} to the OPC UA server')

class SubHandler(object):
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """
    def __init__(self, client, idx, mqttc: mqtt.Client, ids) -> None:
        self.client = client
        self.idx = idx
        self.ids_node = ids
        self.mqttc = mqttc

    def datachange_notification(self, node, val, data):
        '''
        The method that is called whenever a data change event occurs in the OPC UA server.
        '''
        asyncio.create_task(self.handle_change(val))

    async def handle_change(self, val):
        print(f"Raking in progress: {val[LADLE_TILT_STATE_INDEX]}")
        process_ids = await self.ids_node.get_value()
        heat_id = process_ids[HEAT_ID_INDEX]
        if val[LADLE_TILT_STATE_INDEX]: # raking has stated
            # Publish to raking event topic that the raking has started and is in process
            event: dict = {"heat_id": heat_id, "state": val[LADLE_TILT_STATE_INDEX]}
            self.mqttc.publish(EVENT_TOPIC, json.dumps(event), qos=2)

        else:
            # Publish to raking event topic that the raking has completed
            event: dict = {"heat_id": heat_id, "state": val[LADLE_TILT_STATE_INDEX]}
            self.mqttc.publish(EVENT_TOPIC, json.dumps(event), qos=2)

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
            idx = NAMESPACE

            states = client.get_node("ns=2;s=[UA_server]OU_Server_IO.BOOL_Write")
            ids = client.get_node("ns=2;s=[UA_server]OU_Server_IO.REAL_Write")
            data = client.get_node("ns=2;s=[UA_server]OU_Server_IO.REAL_Read")

            handler = SubHandler(client, idx, mqtt_client, ids)

            subscription = await client.create_subscription(500, handler)

            await subscription.subscribe_data_change(states)

            print("Subscription active. Waiting for state changes...")

            # Keep the connection alive
            while True:
                try:
                    # Get value from mqtt
                    try:
                        raking_data = data_queue.get(block=False)
                        heat_id = raking_data["heat_id"]
                        time = raking_data["total_time_seconds"]
                        pulls = raking_data["num_pulls"]
                    except queue.Empty:
                        await asyncio.sleep(1)
                        continue

                    # Read current array
                    real_values = await data.get_value()

                    # Update specific indices

                    # TODO: check that the heat id is the same as the one read and passed
                    real_values[HEAT_ID_INDEX] = float(heat_id)

                    real_values[TIME_INDEX] = float(time)
                    real_values[PULLS_INDEX] = float(pulls)

                    # Write back
                    await data.set_value(real_values, ua.VariantType.Double)
                    print(f"Raking for heat id {heat_id} took {time}s and required {pulls} pulls")
                except Exception as e:
                    print(f"Failed to write: {e}")
                await asyncio.sleep(1)
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())

