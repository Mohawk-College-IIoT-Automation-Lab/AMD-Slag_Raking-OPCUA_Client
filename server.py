#!/home/daniil/miniconda3/envs/opcua/bin/python
import asyncio
import logging

from asyncua import Server, ua

HOSTNAME = "iiot-daniil"

LADLE_TILT_STATE_INDEX = 0 
RAKE_HOME_STATE_INDEX = 1
HEAT_ID_INDEX = 0
TIME_INDEX = 1
PULLS_INDEX = 2


async def main():
    _logger = logging.getLogger(__name__)
    # setup our server
    server = Server()
    await server.init()
    server.set_endpoint(f"opc.tcp://{HOSTNAME}:4990/FactoryTalkLinxGateway/")

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

    # Set array to be writable FOR SIMULATION ONLY
    # Technically this is a read-only array of values provided
    await real_read_list.set_writable()
    await bool_read_list.set_writable()
    _logger.info("Starting server!")
    async with server:
        while True:
            await asyncio.sleep(5)
            states: list = await bool_read_list.get_value()
            ids: list = await real_read_list.get_value()
            data: list = await real_write_list.get_value()
            _logger.info(f"Current Ladle Tilt State: {states[LADLE_TILT_STATE_INDEX]}")
            _logger.info(f"Heat ID read: {ids[HEAT_ID_INDEX]}")
            _logger.info(f"Heat ID processed: {data[HEAT_ID_INDEX]}")
            _logger.info(f"Total Raking Time: {data[TIME_INDEX]} seconds")
            _logger.info(f"Number of pulls: {data[PULLS_INDEX]}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(), debug=True)
