from .peep import PEEPClient, PEEPServer
import playground
from playground.network.common import StackingProtocol, StackingTransport, StackingProtocolFactory

class PassThrough1(StackingProtocol):
    def connection_made(self, transport):
        print(" - PassThrough1 connection_made")
        self.transport = transport
        higherTransport = StackingTransport(transport)
        self.higherProtocol().connection_made(higherTransport)
    
    def data_received(self, data):
        print(" - PassThrough1 data_received")
        self.higherProtocol().data_received(data)
    
    def connection_lost(self, exc):
        print(" - PassThrough1 connection_lost")
        self.transport = None
        self.higherProtocol().connection_lost(exc)

lab2ClientFactory = StackingProtocolFactory(PassThrough1, PEEPClient)
lab2ServerFactory = StackingProtocolFactory(PassThrough1, PEEPServer)

lab2Connector = playground.Connector(protocolStack=(lab2ClientFactory, lab2ServerFactory))
playground.setConnector("Guoye_protocol", lab2Connector)
#playground.setConnector("team7_alt_peep_protocol", lab2Connector)
