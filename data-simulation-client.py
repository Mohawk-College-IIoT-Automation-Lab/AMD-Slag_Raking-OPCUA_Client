import sys, os, shutil
import asyncio, aiomqtt
import json
import random
import consts

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configuration
SAVE_DIR = os.path.join(os.path.expanduser("~"), "Documents", "test_jsons")

# Initialize state
# Global variable to store the generated data
cv_data = {}

# Setup directory: Clear old ones on restart, then create fresh
if os.path.exists(SAVE_DIR):
    shutil.rmtree(SAVE_DIR)
os.makedirs(SAVE_DIR)

print(f"Files will be saved to: {SAVE_DIR}")


# No point of making this function async because it just does math
# It is not waiting for any I/O
# It will still be performed synchronously because it is a CPU task
# to do math, string manipulation, or logic
def generate_random_data():
    """Generates data based on user-specified ranges."""
    steel_start = round(random.random(), 2)
    steel_end = round(random.uniform(3.0, 10.0), 2)
    total_slag_start = round(100.0 - steel_start, 2)
    total_slag_end = round(100.0 - steel_end, 2)
    liquid_slag_start = round(
        random.uniform(total_slag_start * 0.2, total_slag_start * 0.4), 2
    )
    liquid_slag_end = round(
        random.uniform(total_slag_end * 0.2, total_slag_end * 0.4), 2
    )
    data = {
        "total_time_seconds": random.randint(50, 200),
        "num_pulls": random.randint(5, 15),
        "overall": {
            "steel_pct_start": steel_start,
            "steel_pct_end": steel_end,
            "total_slag_pct_start": total_slag_start,
            "total_slag_pct_end": total_slag_end,
            "solid_slag_pct_start": round(total_slag_start - liquid_slag_start, 2),
            "solid_slag_pct_end": round(total_slag_end - liquid_slag_end, 2),
            "liquid_slag_pct_start": liquid_slag_start,
            "liquid_slag_pct_end": liquid_slag_end,
            "slag_index_start": round(random.random(), 4),
            "slag_index_end": round(random.random(), 4),
        },
    }
    return data


async def publish_camera_data(client: aiomqtt.Client):
    while True:
        temp_val = round(random.uniform(50.0, 100.0), 2)
        payload = json.dumps({"connected": True, "temperature": temp_val})
        await client.publish(consts.CAMERA_TOPIC, payload, qos=0)
        await asyncio.sleep(5)


async def on_message(client: aiomqtt.Client):
    global cv_data
    await client.subscribe(consts.EVENT_TOPIC, qos=2)
    async for message in client.messages:
        data = message.payload.decode("utf-8")
        event = json.loads(data)

        # event["state"] is expected to be boolean true/false
        value = event.get("state")
        state = bool(value) if value is not None else None

        if state is True:
            # Generate and Save
            cv_data = generate_random_data()
            file_path = os.path.join(
                SAVE_DIR, f"ladle_{event.get('heat_id', 0):02d}.json"
            )

            with open(file_path, "w") as f:
                json.dump(cv_data, f, indent=2)

            print(f"Generated & Saved: {file_path}")

        elif state is False:
            # Publish
            if cv_data:
                cv_data["heat_id"] = event["heat_id"]
                await client.publish(consts.DATA_TOPIC, json.dumps(cv_data), qos=2)
                print(f"Published latest data to {consts.DATA_TOPIC}")
                cv_data.clear()
            else:
                print("No data staged. Send 'true' first.")

        else:
            print("State key not present in message json")


async def main():
    try:
        async with aiomqtt.Client(consts.BROKER) as client:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(on_message(client))
                tg.create_task(publish_camera_data(client))

    except* aiomqtt.MqttError as eg:
        # eg is an ExceptionGroup containing one or more MqttErrors
        for e in eg.exceptions:
            print(f"MQTT Error: {e}")
    except* Exception as eg:
        print(f"Caught exception group: {eg.exceptions}")
        print("Disconnecting...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Graceful exit on Ctrl+C
        sys.exit(0)

# TODO: Read about async with, async for
# TODO: Read about asyncio.gather and task groups
# TODO: Read about except*, exception groups, and asyncio.CancelledTask
# TODO: Read about if aiofile is worth implementing
