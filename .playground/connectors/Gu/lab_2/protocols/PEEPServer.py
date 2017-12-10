import asyncio

from ...playgroundpackets import PEEPPacket
from ..constants import BASIC_TIMEOUT
from ..transport.PEEPTransport import PEEPTransport
from .PEEP import PEEP


class PEEPServer(PEEP):

    def __init__(self):
        super(PEEPServer, self).__init__()

    def connection_made(self, transport):
        print('---- PEEP server connected ----')
        self.transport = transport

    def data_received(self, data):
        self._deserializer.update(data)
        for data_packet in self._deserializer.nextPackets():
            if isinstance(data_packet, PEEPPacket):
                if self._state == 0:
                    if data_packet.Type == 0:
                        self.handshake_syn_received(data_packet)
                    else:
                        print('PEEP server is waiting for a SYN packet')
                elif self._state == 1:
                    if data_packet.Type == 2:
                        self.handshake_ack_received(data_packet)
                    else:
                        print('PEEP server is waiting for a ACK packet')
                elif self._state == 2:
                    if data_packet.Type == 2:
                        self.ack_received(data_packet)
                    elif data_packet.Type == 3:
                        self.rip_received(data_packet)
                    elif data_packet.Type == 4:
                        self.rip_ack_received(data_packet)
                    elif data_packet.Type == 5:
                        if self._rip_sent:
                            print('PEEP server is waiting for a RIP/RIP-ACK packet')
                        else:
                            self.data_packet_received(data_packet)
                    else:
                        print('PEEP server is waiting for a ACK/DATA packet')

                else:
                    raise ValueError('PEEP server wrong state')
            else:
                print('PEEP server is waiting for a PEEP packet')

    def connection_lost(self, exc):
        self.higherProtocol().connection_lost(exc)

    def handshake_syn_received(self, data_packet):
        if data_packet.verifyChecksum():
            print('PEEP server received SYN.')
            handshake_packet = PEEPPacket.Create_SYN_ACK(data_packet.SequenceNumber)
            self.transport.write(handshake_packet.__serialize__())
            print('PEEP server sent SYN-ACK with seq num %s' % handshake_packet.SequenceNumber)
            asyncio.get_event_loop().call_later(BASIC_TIMEOUT, self.check_flag_packet, handshake_packet)
            self._seq_num_for_handshake = handshake_packet.SequenceNumber
            self._state = 1
            self._seq_num_for_next_expected_packet = handshake_packet.Acknowledgement
            print('expected next pack with seq num %s' % self._seq_num_for_next_expected_packet)
        else:
            print('SYN incorrect checksum.')

    def handshake_ack_received(self, data_packet):
        if data_packet.verifyChecksum():
            if data_packet.Acknowledgement == self._seq_num_for_handshake + 1:
                self._need_flag_packet_resent[1] = False
                print('PEEP Server received ACK')
                self.higherProtocol().connection_made(PEEPTransport(self.transport, self))
                self._state = 2
            else:
                print('Incorrect sequence number.')
        else:
            print('ACK incorrect checksum')

