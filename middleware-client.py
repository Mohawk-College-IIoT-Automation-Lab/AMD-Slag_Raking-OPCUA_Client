#!/home/daniil/miniconda3/envs/opcua/bin/python
import asyncio, aiomqtt
import consts
import json
from asyncua import Client, ua
from asyncua.client.client import Subscription
from asyncua.server import event_generator

URL = f"opc.tcp://{consts.HOSTNAME}:4990/FactoryTalkLinxGateway/"

class SubHandler(object):
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """
    def __init__(self, mqttc: aiomqtt.Client, ids) -> None:
        self.ids_node = ids
        self.mqttc = mqttc

    def datachange_notification(self, node, val, data):
        '''
        The method that is called whenever a data change event occurs in the OPC UA server.
        '''
        asyncio.create_task(self.handle_change(val))

    async def handle_change(self, val):
        tilt_state = val[consts.LADLE_TILT_STATE_INDEX]
        print(f"Raking in progress: {tilt_state}")
        process_ids = await self.ids_node.get_value()
        heat_id = int(process_ids[consts.HEAT_ID_INDEX])
        if tilt_state: # raking has stated
            # Publish to raking event topic that the raking has started and is in process
            event: dict = {"heat_id": heat_id, "state": tilt_state}
            await self.mqttc.publish(consts.EVENT_TOPIC, json.dumps(event), qos=2)

        else:
            # Publish to raking event topic that the raking has completed
            event: dict = {"heat_id": heat_id, "state": tilt_state}
            await self.mqttc.publish(consts.EVENT_TOPIC, json.dumps(event), qos=2)

async def handle_mqtt_messages(mqtt_client: aiomqtt.Client, opc_data_node, opc_flags_node):
    await mqtt_client.subscribe(consts.DATA_TOPIC, qos=2)
    await mqtt_client.subscribe(consts.CAMERA_TOPIC, qos=2)

    async for message in mqtt_client.messages:
        try:
            mqtt_data = json.loads(message.payload.decode())
            real_values = await opc_data_node.get_value()
            bool_values = await opc_flags_node.get_value()

            if message.topic.value == consts.DATA_TOPIC:
                    # TODO: check that the heat id is the same as the one read and passed
                    real_values[consts.HEAT_ID_INDEX] = float(mqtt_data["heat_id"])

                    real_values[consts.TIME_INDEX] = float(mqtt_data["total_time_seconds"])
                    real_values[consts.PULLS_INDEX] = float(mqtt_data["num_pulls"])
                    real_values[consts.STEEL_START_INDEX] = mqtt_data["overall"]["steel_pct_start"]
                    real_values[consts.STEEL_END_INDEX] = mqtt_data["overall"]["steel_pct_end"]
                    real_values[consts.TOTAL_SLAG_START_INDEX] = mqtt_data["overall"]["total_slag_pct_start"]
                    real_values[consts.TOTAL_SLAG_END_INDEX] = mqtt_data["overall"]["total_slag_pct_end"]
                    real_values[consts.SOLID_SLAG_START_INDEX] = mqtt_data["overall"]["solid_slag_pct_start"]
                    real_values[consts.SOLID_SLAG_END_INDEX] = mqtt_data["overall"]["solid_slag_pct_end"]
                    real_values[consts.LIQUID_SLAG_START_INDEX] = mqtt_data["overall"]["liquid_slag_pct_start"]
                    real_values[consts.LIQUID_SLAG_END_INDEX] = mqtt_data["overall"]["liquid_slag_pct_end"]
                    real_values[consts.SLAG_START_INDEX] = mqtt_data["overall"]["slag_index_start"]
                    real_values[consts.SLAG_END_INDEX] = mqtt_data["overall"]["slag_index_end"]
                    print(f"Raking for heat id {mqtt_data["heat_id"]} took {mqtt_data["total_time_seconds"]}s and required {mqtt_data["num_pulls"]} pulls")

            elif message.topic.value == consts.CAMERA_TOPIC:
                    real_values[consts.CAMERA_TEMPERATURE_INDEX] = mqtt_data["temperature"]
                    bool_values[consts.CAMERA_STATUS_INDEX] = mqtt_data["connected"]

            await opc_data_node.set_value(real_values, ua.VariantType.Double)
            await opc_flags_node.set_value(bool_values, ua.VariantType.Boolean)

        except Exception as e:
            print(f"Failed to process MQtt message or write to OPC: {e}")

async def main():
    print(f"Connecting to MQTT Broker at {consts.BROKER}")
    async with aiomqtt.Client(consts.BROKER, consts.PORT) as mqtt_client:

        print(f"Connecting to OPC Server at {URL} ...")
        async with Client(url=URL) as opc_client:

            states_node = opc_client.get_node("ns=2;s=[UA_server]OU_Server_IO.BOOL_Write")
            ids_node = opc_client.get_node("ns=2;s=[UA_server]OU_Server_IO.REAL_Write")
            data_node = opc_client.get_node("ns=2;s=[UA_server]OU_Server_IO.REAL_Read")
            flags_node = opc_client.get_node("ns=2;s=[UA_server]OU_Server_IO.BOOL_Read") 

            handler = SubHandler(mqtt_client, ids_node)
            subscription = await opc_client.create_subscription(500, handler)
            print("Subscription active. Waiting for state changes...")

            await subscription.subscribe_data_change(states_node)
            await handle_mqtt_messages(mqtt_client, data_node, flags_node)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
