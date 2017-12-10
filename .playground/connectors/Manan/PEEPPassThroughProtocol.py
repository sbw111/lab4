import random

from .PEEP import PEEP
from .PEEPPackets import PEEPPacket
from .PEEP import PeepTransport
from playground.network.common import StackingProtocolFactory


class PeepClient(PEEP):
    INIT, HANDSHAKE, TRANS, TEARDOWN = [0, 1, 2, 3]

    def __init__(self):
        super().__init__()

    def connection_made(self, transport):
        self.transport = transport
        self.deserializer = PEEPPacket.Deserializer()
        self.start_handshake()

    def handle_syn(self, packet):
        raise Exception("Unexpected SYN")

    def start_handshake(self):
        print("Client Handshake start")

        self.sequence_number = random.randint(0, 2 ** 16)
        packet = PEEPPacket()
        packet.Type = PEEPPacket.SYN
        # packet.Data = "piggyback".encode()
        packet.SequenceNumber = self.sequence_number
        packet.updateChecksum()
        self.send_packet(packet)
        self.state = PeepClient.HANDSHAKE


class PeepServer(PEEP):
    INIT, HANDSHAKE, TRANS, TEARDOWN = [0, 1, 2, 3]

    def __init__(self):
        super().__init__()

    def connection_made(self, transport):
        print("peep_server: connection made")
        self.transport = transport
        self.higherProtocol().transport = PeepTransport(transport, self)
        self.deserializer = PEEPPacket.Deserializer()

    def handle_synack(self, packet):
        raise Exception("Unexpected SYN")

    def handle_ack(self, packet):
        if self.state == PeepServer.HANDSHAKE:
            print('server : handshake complete')
            self.state = PeepServer.TRANS
            self.sequence_number = packet.Acknowledgement
            self.base_sequence_number = self.sequence_number
            self.higherProtocol().connection_made(PeepTransport(self.transport, self))
        else:
            super().handle_ack(packet)


clientFactory = StackingProtocolFactory(PeepClient)
serverFactory = StackingProtocolFactory(PeepServer)
