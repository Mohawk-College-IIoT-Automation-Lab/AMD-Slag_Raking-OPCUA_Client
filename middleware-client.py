#!/home/daniil/miniconda3/envs/opcua/bin/python
import asyncio

from asyncua import Client

url = "opc.tcp://localhost:4840/freeopcua/server/"
namespace = "http://examples.freeopcua.github.io"


async def main():
    print(f"Connecting to {url} ...")
    async with Client(url=url) as client:

        root = client.get_root_node()
        print(f"Root node is {root}")
        # Find the namespace index
        nsidx = await client.get_namespace_index(namespace)
        print(f"Namespace Index for '{namespace}': {nsidx}")

        # Get the stateiable node for read / write
        line = await client.nodes.objects.get_child(f"{nsidx}:PLine")
        print(f"PLine node: {line}")
        state = await client.nodes.root.get_child(f"0:Objects/{nsidx}:PLine/{nsidx}:State")
        print(f"Node: {state}")
        print(f"Full value of node: {await state.read_data_value()}")
        value = await state.read_value()
        print(f"Value of Speed ({state}): {value}")

        new_value = value - 50
        print(f"Setting value of Speed to {new_value} ...")
        await state.write_value(new_value)

        # Calling a method
        res = await client.nodes.objects.call_method(f"{nsidx}:ServerMethod", 5)
        print(f"Calling ServerMethod returned {res}")


if __name__ == "__main__":
    asyncio.run(main())
