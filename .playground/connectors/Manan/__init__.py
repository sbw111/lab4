import playground
from .PEEPPassThroughProtocol import clientFactory, serverFactory

lab2Connector = playground.Connector(protocolStack=(clientFactory, serverFactory))
playground.setConnector("Manan_protocol", lab2Connector)
