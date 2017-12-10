from playground.network.common.Protocol import StackingProtocol, StackingTransport


class PEEPClientApplication(StackingProtocol):
    def __init__(self):
        super().__init__()

    def connection_made(self, transport):
        print("CONN sbc")
        self.transport = transport
        self.lowerTransport().sendPacket()

    def data_received(self, data):
        print("DATA RECD")

    def connection_lost(self, exc):
        print("CONN")


    def write_data(self, data):
        print("WRITE")
        self.transport.write(data)