#!/home/daniil/miniconda3/envs/opcua/bin/python
import asyncio
import logging
import consts

from asyncua import Server, ua


async def main():
    _logger = logging.getLogger(__name__)
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint(f"opc.tcp://{consts.HOSTNAME}:4990/FactoryTalkLinxGateway/")

    # populating our address space
    # Creating a parent object to put all the variables under
    ua_server = await server.nodes.objects.add_object(nodeid="ns=2;i=1", bname = "UA_server",)
    
    # Variable node for states
    bool_read_list = await ua_server.add_variable(
            nodeid="ns=2;s=[UA_server]OU_Server_IO.BOOL_Write",
            bname="[UA_server]OU_Server_IO.BOOL_Write",
            val=[False]*96,
            varianttype=ua.VariantType.Boolean,
            )

    # Variable node for flags
    bool_write_list = await ua_server.add_variable(
            nodeid="ns=2;s=[UA_server]OU_Server_IO.BOOL_Read",
            bname="[UA_server]OU_Server_IO.BOOL_Read",
            val=[False]*96,
            varianttype=ua.VariantType.Boolean,
            )

    # Variable node with CV data
    real_write_list = await ua_server.add_variable(
            nodeid="ns=2;s=[UA_server]OU_Server_IO.REAL_Read",
            bname="[UA_server]OU_Server_IO.REAL_Read",
            val=[0.0]*50,
            varianttype=ua.VariantType.Double,
            )

    # Vaiable node supplemental data
    real_read_list = await ua_server.add_variable(
            nodeid="ns=2;s=[UA_server]OU_Server_IO.REAL_Write",
            bname="[UA_server]OU_Server_IO.REAL_Write",
            val=[0.0]*50,
            varianttype=ua.VariantType.Double,
            )

    
    # Set array to be writable by clients
    # This array will be used to publish CV data
    await real_write_list.set_writable()
    await bool_write_list.set_writable()

    # Set array to be writable FOR SIMULATION ONLY
    # Technically this is a read-only array of values provided
    await real_read_list.set_writable()
    await bool_read_list.set_writable()
    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(5)
            states: list = await bool_read_list.get_value()
            flags: list = await bool_write_list.get_value()
            ids: list = await real_read_list.get_value()
            data: list = await real_write_list.get_value()
            _logger.info(f"Ladle Tilted: {bool(states[consts.LADLE_TILT_STATE_INDEX])}")
            _logger.info(f"Heat ID read: {int(ids[consts.HEAT_ID_INDEX])}")
            _logger.info(f"Heat ID processed: {int(data[consts.HEAT_ID_INDEX])}")
            _logger.info(f"Total Raking Time: {data[consts.TIME_INDEX]} seconds")
            _logger.info(f"Number of pulls: {int(data[consts.PULLS_INDEX])}")
            _logger.info(f"Camera Connected: {bool(flags[consts.CAMERA_STATUS_INDEX])}")
            _logger.info(f"Camera Temperature: {data[consts.CAMERA_TEMPERATURE_INDEX]}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(), debug=True)
