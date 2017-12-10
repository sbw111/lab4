# import connectors.WHOAMI
# import connectors.Gu
# import playground
# from .WHOAMI.lab2.src.lab2_protocol import *
# from .WHOAMI.lab3.src.lab3_protocol import *
# from .Gu.lab_2.factory.PEEPFactory import get_lab2_client_factory, get_lab2_server_factory
# from playground.network.common import StackingProtocolFactory


# cf1 = StackingProtocolFactory(lambda: PEEPClientProtocol())
# sf1 = StackingProtocolFactory(lambda: PEEPServerProtocol())
# lab_connector1 = playground.Connector(protocolStack=(cf1, sf1))


# playground.setConnector('WHOAMI_protocol', lab_connector1)

# cf2 = get_lab2_client_factory()
# sf2 = get_lab2_server_factory()
# lab_connector2 = playground.Connector(protocolStack=(cf2, sf2))

# playground.setConnector('Gu_protocol', lab_connector2)
