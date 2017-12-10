import asyncio
import random
import playground
from .PEEPPackets import PEEPPacket
from playground.network.common import StackingProtocol, StackingTransport, StackingProtocolFactory
from playground.network.packet import PacketType, FIELD_NOT_SET
from playground.common import Timer, Seconds


class PEEP(StackingProtocol):
    INIT, HANDSHAKE, TRANS, TEARDOWN = [0, 1, 2, 3]

    def __init__(self):
        super().__init__()
        self.state = PEEP.INIT
        self.window_size = 100
        self.chunk_size = 1024
        self.transport = None
        self.deserializer = None
        self.base_sequence_number = None
        self.sequence_number = None
        self.expected_sequence_number = None
        self.send_window_start = None
        self.send_window_end = None
        self.receive_window_start = None
        self.receive_window_end = None
        self.data_size = 0
        self.data = bytes()
        self.timers = []
        self.received_data = []
        self.rip_timer = None
        self.rip_sequence_number = None
        self.piggyback = False
        self.acknowledgement = None

    def data_received(self, data):
        print("data received")
        self.deserializer.update(data)
        for packet in self.deserializer.nextPackets():
            if isinstance(packet, PEEPPacket) and packet.verifyChecksum():
                self.handle_packets(packet)

    def handle_packets(self, packet):
        packet_type = packet.Type
        if packet_type == PEEPPacket.SYN and self.state == PEEP.INIT:
            print('received SYN')
            self.handle_syn(packet)
        elif packet_type == PEEPPacket.SYNACK and self.state == PEEP.HANDSHAKE:
            print('received SYNACK')
            self.handle_synack(packet)
        elif packet_type == PEEPPacket.ACK:
            print("received ACK")
            self.handle_ack(packet)
        elif packet_type == PEEPPacket.DATA and (self.state == PEEP.TRANS or self.state == PEEP.TEARDOWN):
            print('received Data')
            self.handle_data(packet)
        elif packet_type == PEEPPacket.RIP and (self.state == PEEP.TRANS or self.state == PEEP.TEARDOWN):
            print('received RIP')
            self.handle_rip(packet)
        elif packet_type == PEEPPacket.RIPACK and self.state == PEEP.TEARDOWN:
            print('received RIP-ACK')
            self.handle_ripack()
        else:
            print('BAD PACKET. summary: ', packet.__repr__())

    def handle_syn(self, packet):
        print('checksum of SYN is correct')
        packetback = PEEPPacket()
        if packet.Data != FIELD_NOT_SET and packet.Data.decode() == "piggyback":
            print("syn: enable piggybacking")
            packetback.Data = "piggyback".encode()
            self.piggyback = True
        packetback.Acknowledgement = packet.SequenceNumber + 1
        self.sequence_number = random.randint(0, 2 ** 16)
        self.base_sequence_number = self.sequence_number + 1
        self.expected_sequence_number = packet.SequenceNumber + 1
        self.send_window_start = self.base_sequence_number
        self.send_window_end = self.base_sequence_number
        packetback.SequenceNumber = self.sequence_number
        packetback.Type = PEEPPacket.SYNACK
        packetback.updateChecksum()
        self.send_packet(packetback)
        self.state = PEEP.HANDSHAKE
        print('sent SYNACK')

    def handle_synack(self, packet):
        print("Received synack")
        if packet.Data != FIELD_NOT_SET and packet.Data.decode() == "piggyback":
            print("synack: enable piggybacking")
            self.piggyback = True
        packet_to_send = PEEPPacket()
        packet_to_send.Type = PEEPPacket.ACK
        packet_to_send.SequenceNumber = packet.Acknowledgement
        packet_to_send.Acknowledgement = packet.SequenceNumber + 1
        packet_to_send.updateChecksum()
        self.base_sequence_number = packet.Acknowledgement
        self.expected_sequence_number = packet.SequenceNumber + 1
        self.send_window_start = self.base_sequence_number
        self.send_window_end = self.base_sequence_number
        self.sequence_number = self.base_sequence_number
        print("Sending Back Ack")
        self.send_packet(packet_to_send)
        self.state = PEEP.TRANS  # transmission state
        # Open upper layer transport
        print("connection_made to higher protocol")
        self.higherProtocol().connection_made(PeepTransport(self.transport, self))

    def handle_ack(self, packet):
        if self.piggyback and packet.Data != FIELD_NOT_SET and len(packet.Data) > 0:
            self.handle_data(packet)
        self.acknowledgement = packet.Acknowledgement
        print("ack: ", packet.Acknowledgement)
        i = 0
        while i < len(self.timers):
            timer = self.timers[i]
            if timer._callbackArgs[0].SequenceNumber < packet.Acknowledgement:
                timer.cancel()
                self.timers = self.timers[:i] + self.timers[i + 1:]
                i -= 1
            i += 1

        if self.rip_timer is not None:
            self.rip_timer.cancel()
            self.rip_timer.extend(Seconds(2))
            self.rip_timer.start()
            return

        self.send_window_start = max(self.send_window_start, packet.Acknowledgement)
        self.send_window_data()

        if self.state == PEEP.TEARDOWN and self.sent_all():
            self.send_rip()
            self.rip_timer = Timer(Seconds(2), self.abort_connection)
            self.rip_timer.start()

    def handle_data(self, packet):
        self.received_data.append(packet)
        if packet.SequenceNumber == self.expected_sequence_number:
            self.pass_data_up()

        ack_packet = PEEPPacket()
        if self.piggyback:
            try_getting_piggyback_data = self.get_piggyback_data()
            if try_getting_piggyback_data is not None:
                ack_packet.Data = try_getting_piggyback_data
                ack_packet.SequenceNumber = self.get_piggyback_sequence_number()

        ack_packet.Acknowledgement = self.expected_sequence_number
        ack_packet.Type = PEEPPacket.ACK
        ack_packet.updateChecksum()
        print("Sending ACK")
        self.send_packet(ack_packet)

        if self.state == PEEP.TEARDOWN and self.received_all():
            self.send_rip_ack(self.rip_sequence_number + 1)

    def initiate_teardown(self):
        print('Start TEARDOWN')
        self.state = PEEP.TEARDOWN
        if self.sent_all():
            self.send_rip()
            self.rip_timer = Timer(Seconds(2), self.abort_connection)
            self.rip_timer.start()

    def received_all(self):
        return self.rip_sequence_number == self.expected_sequence_number

    def sent_all(self):
        return self.sequence_number - self.base_sequence_number >= self.data_size

    def get_piggyback_data(self):
        if self.sequence_number - self.base_sequence_number >= self.data_size:
            i = self.sequence_number - self.base_sequence_number
            ret = self.data[i:min(i + self.chunk_size, self.send_window_start + self.window_size * self.chunk_size)]
            self.sequence_number += len(ret)
            self.send_window_end += len(ret)
            return ret

    def get_piggyback_sequence_number(self):
        return self.sequence_number

    def transmit_data(self, data):
        self.data += data
        self.data_size += len(data)
        print("transmitting data size: ", self.data_size)
        self.send_window_data()

    def send_window_data(self):
        print('Sending Window Data')
        while self.send_window_end - self.send_window_start < self.window_size * self.chunk_size:
            if self.sequence_number - self.base_sequence_number >= self.data_size:
                print("Everything sent")
                return
            self.send_next_chunk()

    def pass_data_up(self):
        self.received_data.sort(key=lambda current_packet: current_packet.SequenceNumber)
        i = 0
        while i < len(self.received_data):
            packet = self.received_data[i]
            if packet.SequenceNumber == self.expected_sequence_number:
                self.higherProtocol().data_received(packet.Data)
                self.expected_sequence_number += len(packet.Data)
                self.received_data = self.received_data[:i] + self.received_data[i + 1:]
                i -= 1
            i += 1

    def send_next_chunk(self):
        print('send next chunk')
        next_packet = PEEPPacket()
        i = self.sequence_number - self.base_sequence_number
        next_packet.Type = PEEPPacket.DATA
        next_packet.SequenceNumber = self.sequence_number
        next_packet.Data = self.data[
                           i:min(i + self.chunk_size, self.send_window_start + self.window_size * self.chunk_size)]
        next_packet.updateChecksum()
        print("Now sending packet with seq number:", next_packet.SequenceNumber)
        self.send_packet(next_packet)
        self.sequence_number += len(next_packet.Data)
        self.send_window_end += len(next_packet.Data)

    def connection_made(self, transport):
        raise NotImplementedError

    def connection_lost(self, exc):
        self.transport.close()
        self.transport = None
        asyncio.get_event_loop().stop()

    def send_packet(self, packet):
        print(self, "send packet: ", packet)
        self.transport.write(packet.__serialize__())
        if packet.Type != PEEPPacket.SYN and packet.Type != PEEPPacket.DATA and packet.Type != PEEPPacket.RIP:
            return
        timer = Timer(Seconds(1), self.send_packet, packet)
        self.timers.append(timer)
        timer.start()

    """
        RIP's and TEARDOWN 
    """

    def handle_rip(self, packet):
        self.state = PEEP.TEARDOWN
        self.rip_sequence_number = packet.SequenceNumber
        if self.received_all():
            self.send_rip_ack(self.rip_sequence_number + 1)

    def send_rip(self):
        print("Sending RIP")
        rip_packet = PEEPPacket(Type=PEEPPacket.RIP)
        rip_packet.SequenceNumber = self.sequence_number
        self.sequence_number += 1
        rip_packet.updateChecksum()
        self.send_packet(rip_packet)

    def send_rip_ack(self, ack):
        print("Sending RIP ACK")
        rip_ack_packet = PEEPPacket(Type=PEEPPacket.RIPACK)
        rip_ack_packet.Acknowledgement = ack
        rip_ack_packet.updateChecksum()
        self.send_packet(rip_ack_packet)

    def handle_ripack(self):
        self.transport.close()

    def abort_connection(self):
        self.transport.close()


class PeepTransport(StackingTransport):
    def __init__(self, transport, protocol):
        super().__init__(transport)
        self._lowerTransport = transport
        self.protocol = protocol
        self.transport = self._lowerTransport

    def write(self, data):
        print("Write to PEEP trans")
        self.protocol.transmit_data(data)

    def close(self):
        print("Close PEEP trans")
        self.protocol.initiate_teardown()

    def abort(self):
        self.protocol.abort_connection()
