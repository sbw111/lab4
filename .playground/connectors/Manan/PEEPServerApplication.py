from playground.network.common.Protocol import StackingProtocol, StackingTransport


class PEEPServerApplication(StackingProtocol):
    def __init__(self):
        super().__init__()

    def connection_made(self, transport):
        print("CONN")
        self.transport = transport

    def data_received(self, data):
        print("DATA RECD")
        print(data)

    def connection_lost(self, exc):
        print("CONN")


    def write_data(self, data):
        print("WRITE")
        self.transport.write(data)