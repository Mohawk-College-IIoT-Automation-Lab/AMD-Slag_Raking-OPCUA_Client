#!/home/daniil/miniconda3/envs/opcua/bin/python
import asyncio
import logging
import consts

from asyncua import Server, ua, Node


async def main():
    _logger = logging.getLogger(__name__)
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint(consts.ENDPOINT)

    # populating our address space
    # Creating a parent object to put all the variables under
    ua_server = await server.nodes.objects.add_object(nodeid="ns=2;i=1", bname = "UA_server",)
    
    # Variable node for states
    rake_home_node = await ua_server.add_variable(
            nodeid=consts.RAKE_HOME_STATE_NODEID,
            bname="Rake Home State",
            val= True,
            varianttype=ua.VariantType.Boolean,
            )

    ladle_tilt_node = await ua_server.add_variable(
            nodeid=consts.LADLE_TILT_STATE_NODEID,
            bname="Ladle Tilt State",
            val= False,
            varianttype=ua.VariantType.Boolean,
            )

    # Variable node for flags
    camera_connection_node = await ua_server.add_variable(
            nodeid=consts.CAMERA_STATUS_NODEID,
            bname="Camera Connection Flag",
            val=True,
            varianttype=ua.VariantType.Boolean,
            )

    # Vaiable node supplemental data
    heat_id_node = await ua_server.add_variable(
            nodeid=consts.HEAT_ID_NODEID,
            bname="Heat ID",
            val=0.0,
            varianttype=ua.VariantType.Double,
            )

    real_write_nodes: list[Node] = []
    # Variable node with CV data
    for i in range(0, 14):
        real_write_nodes.append(await ua_server.add_variable(
                nodeid=f"ns=2;s=[UA_server]OU_Server_IO.REAL_Read[{i:02d}]",
                bname=f"[UA_server]OU_Server_IO.REAL_Read[{i:02d}]",
                val=0.0,
                varianttype=ua.VariantType.Double,
                ))

    
    # Set array to be writable by clients
    # This array will be used to publish CV data
    for real in real_write_nodes:
        await real.set_writable()
    await camera_connection_node.set_writable()

    # Set array to be writable FOR SIMULATION ONLY
    # Technically this is a read-only array of values provided
    await heat_id_node.set_writable()
    await rake_home_node.set_writable()
    await ladle_tilt_node.set_writable()

    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(5)
            rake_state: bool = await rake_home_node.get_value()
            ladle_state: bool = await ladle_tilt_node.get_value()
            camera_connected: bool = await camera_connection_node.get_value()
            id = await heat_id_node.get_value()
            data: list = [await node.get_value() for node in real_write_nodes]
            _logger.info(f"Ladle Tilted: {ladle_state}")
            _logger.info(f"Rake Home: {rake_state}")
            _logger.info(f"Heat ID read: {int(id)}")
            _logger.info(f"Heat ID processed: {int(data[consts.HEAT_ID_INDEX])}")
            _logger.info(f"Total Raking Time: {data[consts.TIME_INDEX]} seconds")
            _logger.info(f"Steel percentage changed from: {data[consts.STEEL_START_INDEX]}% to {data[consts.STEEL_END_INDEX]}%")
            _logger.info(f"Liquid slag percentage changed from: {data[consts.LIQUID_SLAG_START_INDEX]}% to {data[consts.LIQUID_SLAG_END_INDEX]}%")
            _logger.info(f"Number of pulls: {int(data[consts.PULLS_INDEX])}")
            _logger.info(f"Camera Connected: {camera_connected}")
            _logger.info(f"Camera Temperature: {data[consts.CAMERA_TEMPERATURE_INDEX]}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(), debug=True)
