from playground.network.common import StackingTransport


class PLSTransport(StackingTransport):

    def __init__(self, lowerTransport, protocol):
        super(PLSTransport, self).__init__(lowerTransport)
        self._protocol = protocol

    def write(self, data):
        self._protocol.process_data(data)
