from playground.network.common import StackingTransport


class PEEPTransport(StackingTransport):

    def __init__(self, lowerTransport, protocol):
        super().__init__(lowerTransport)
        self._protocol = protocol

    def write(self, data):
        self._protocol.process_data(data)

    def close(self):
        self._protocol.end_session()
