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

        # Get the variable node for read / write
        var = await client.nodes.root.get_child(f"0:Objects/{nsidx}:Motor/{nsidx}:Speed")
        print(f"Node: {var}")
        print(f"Full value of node: {await var.read_data_value()}")
        value = await var.read_value()
        print(f"Value of Speed ({var}): {value}")

        new_value = value - 50
        print(f"Setting value of Speed to {new_value} ...")
        await var.write_value(new_value)

        # Calling a method
        res = await client.nodes.objects.call_method(f"{nsidx}:ServerMethod", 5)
        print(f"Calling ServerMethod returned {res}")


if __name__ == "__main__":
    asyncio.run(main())
