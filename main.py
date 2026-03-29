import asyncio, aiomqtt
import consts
import json
import sys
import logging
from asyncua import Client, ua, Node

logging.basicConfig(
    format="%(levelname)s: %(message)s [%(asctime)s]",
    datefmt="%Y/%m/%d %H:%M:%S",
    level=logging.INFO,
    handlers=[logging.FileHandler("logs.log"), logging.StreamHandler(sys.stdout)],
)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class SubHandler(object):
    """
    The SubscriptionHandler is used to handle the data that is received for the subscription.
    """

    def __init__(self, mqttc: aiomqtt.Client, heat_id: Node) -> None:
        self.heat_id: Node = heat_id
        self.mqttc = mqttc
        # Set of tasks to avoid garbage collection
        self.background_tasks = set()
        self.last_state = None

    def datachange_notification(self, node, val, data):
        """
        The method that is called whenever a data change event occurs in the OPC UA server.
        """
        task = asyncio.create_task(self.handle_change(val))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def handle_change(self, val):
        try:
            state = not bool(val)
            if state == self.last_state:
                return
            self.last_state = state
            logging.info(f"Raking in progress: {state}")
            process_id = int(await self.heat_id.get_value())
            event: dict = {"heat_id": process_id, "state": state}
            await self.mqttc.publish(consts.EVENT_TOPIC, json.dumps(event), qos=2)
        except ua.uaerrors.BadNodeIdUnknown as e:
            logging.error(f"{e}. Node {self.heat_id} doesn't exist")
        except Exception:
            logging.error(
                f"Unexpected failure during OPC UA handle change callback",
                exc_info=True,
            )


async def handle_mqtt_messages(
    mqtt_client: aiomqtt.Client, data_nodes: list[Node], camera_connection_node: Node
):
    await mqtt_client.subscribe(consts.DATA_TOPIC, qos=2)
    await mqtt_client.subscribe(consts.CAMERA_TOPIC, qos=2)
    logging.info(f"Subscribed to {consts.DATA_TOPIC} and {consts.CAMERA_TOPIC} topics")

    async for message in mqtt_client.messages:
        try:
            payload = message.payload.decode()
            mqtt_data = json.loads(payload)
            process_results = [await node.get_value() for node in data_nodes]

            if message.topic.value == consts.DATA_TOPIC:
                # TODO: check that the heat id is the same as the one read and passed
                process_results[consts.HEAT_ID_INDEX] = float(mqtt_data["heat_id"])

                process_results[consts.TIME_INDEX] = float(
                    mqtt_data["total_time_seconds"]
                )
                process_results[consts.PULLS_INDEX] = float(mqtt_data["num_pulls"])
                process_results[consts.STEEL_START_INDEX] = mqtt_data["overall"][
                    "steel_pct_start"
                ]
                process_results[consts.STEEL_END_INDEX] = mqtt_data["overall"][
                    "steel_pct_end"
                ]
                process_results[consts.TOTAL_SLAG_START_INDEX] = mqtt_data["overall"][
                    "total_slag_pct_start"
                ]
                process_results[consts.TOTAL_SLAG_END_INDEX] = mqtt_data["overall"][
                    "total_slag_pct_end"
                ]
                process_results[consts.SOLID_SLAG_START_INDEX] = mqtt_data["overall"][
                    "solid_slag_pct_start"
                ]
                process_results[consts.SOLID_SLAG_END_INDEX] = mqtt_data["overall"][
                    "solid_slag_pct_end"
                ]
                process_results[consts.LIQUID_SLAG_START_INDEX] = mqtt_data["overall"][
                    "liquid_slag_pct_start"
                ]
                process_results[consts.LIQUID_SLAG_END_INDEX] = mqtt_data["overall"][
                    "liquid_slag_pct_end"
                ]
                process_results[consts.SLAG_START_INDEX] = mqtt_data["overall"][
                    "slag_index_start"
                ]
                process_results[consts.SLAG_END_INDEX] = mqtt_data["overall"][
                    "slag_index_end"
                ]
                logging.info(
                    f"Raking for heat id {mqtt_data['heat_id']} took {mqtt_data['total_time_seconds']}s and required {mqtt_data['num_pulls']} pulls"
                )

            elif message.topic.value == consts.CAMERA_TOPIC:
                process_results[consts.CAMERA_TEMPERATURE_INDEX] = mqtt_data[
                    "temperature"
                ]
                camera_connected = mqtt_data["connected"]
                await camera_connection_node.set_value(
                    value=camera_connected, varianttype=ua.VariantType.Boolean
                )

            for idx, result in enumerate(process_results):
                await data_nodes[idx].set_value(
                    value=result, varianttype=ua.VariantType.Double
                )

            logging.info(f"Successfully wrote the result to OPC UA server: {mqtt_data}")

        except KeyError as e:
            logging.error(f"Missing expected key {e} on topic: {message.topic.value}")
        except ValueError as e:
            logging.error(f"Data type conversion failed: {e}")
        except ua.uaerrors.BadNodeIdUnknown as e:
            logging.error(f"Unknown Node ID error: {e}")
        except ua.UaStatusCodeError:
            logging.error(f"Failed to write to OPC", exc_info=True)
        except Exception:
            logging.error(
                f"Unexpected failure during MQTT message handling", exc_info=True
            )


async def main():
    try:
        logging.info(f"Connecting to MQTT Broker at {consts.BROKER}")
        async with aiomqtt.Client(consts.BROKER, consts.PORT) as mqtt_client:
            logging.info(f"Connected to MQTT Broker")

            logging.info(f"Connecting to OPC Server at {consts.ENDPOINT} ...")
            async with Client(url=consts.ENDPOINT) as opc_client:
                logging.info(f"Connected to OPC Server")

                rake_home_node: Node = opc_client.get_node(
                    consts.RAKE_HOME_STATE_NODEID
                )
                heat_id_node: Node = opc_client.get_node(consts.HEAT_ID_NODEID)
                camera_connection_node: Node = opc_client.get_node(
                    consts.CAMERA_STATUS_NODEID
                )
                data_nodes: list[Node] = [
                    opc_client.get_node(
                        f"ns=2;s=[UA_server]OU_Server_IO.REAL_Read[{i:02d}]"
                    )
                    for i in range(0, 14)
                ]

                handler = SubHandler(mqttc=mqtt_client, heat_id=heat_id_node)
                subscription = await opc_client.create_subscription(1000, handler)
                logging.info("Subscription active. Waiting for state changes...")

                await subscription.subscribe_data_change(rake_home_node)
                await handle_mqtt_messages(
                    mqtt_client, data_nodes, camera_connection_node
                )
    except ua.UaStatusCodeError as e:
        logging.critical(f"Error while subscribing to OPC UA tag data changes: {e}")
    except ua.UaError:
        logging.critical("Error while connecting to OPC UA server", exc_info=True)
    except aiomqtt.MqttError:
        logging.critical("Error while connecting to MQTT Broker", exc_info=True)
    except Exception:
        logging.critical("Unexpected error during startup", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
