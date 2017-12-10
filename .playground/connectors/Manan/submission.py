import asyncio
import sys

import playground

from netsec_fall2017.lab2.src.lab2_protocol import PEEPProtocolFactory
from netsec_fall2017.lab2.src.lab2_protocol.PEEPClient import PEEPClient

from netsec_fall2017.lab2.src.lab2_protocol.PEEPServer import PEEPServer


def test():
    ptConnector = playground.Connector(protocolStack=(
    PEEPProtocolFactory.get_client_factory(), PEEPProtocolFactory.get_server_factory()))

    playground.setConnector("PT1", ptConnector)
if __name__ == '__main__':
    test()
    mode = sys.argv[1]
    print (mode)
    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)

    if mode.lower() == "server":
        coro = playground.getConnector("PT1").create_playground_server(lambda: PEEPServer(), 101)
        server = loop.run_until_complete(coro)
        print("Echo Server Started at {}".format(server.sockets[0].gethostname()))
        loop.run_forever()
        loop.close()

    elif mode.lower() == "client":
        coro = playground.getConnector("PT1").create_playground_connection(lambda: PEEPClient(), "20174.1.1.1", 101)
        xPort, client = loop.run_until_complete(coro)
        loop.run_forever()
        loop.close()



