import random, zlib, functools
from playground.network.packet.fieldtypes.attributes import Optional
from playground.network.packet.fieldtypes import UINT8, UINT16, UINT32, BUFFER
from playground.network.packet import PacketType
from playground.common import CustomConstant as Constant


@functools.total_ordering
class PEEPPacket(PacketType):
    DEFINITION_IDENTIFIER = 'peep.packet'
    DEFINITION_VERSION = '1.2'

    FIELDS = [
        ('Type', UINT8),
        ('SequenceNumber', UINT32({Optional: True})),
        ('Checksum', UINT16),
        ("Acknowledgement", UINT32({Optional: True})),
        ("Data", BUFFER({Optional: True}))
    ]

    # Type
    SYN = Constant(intValue=0, strValue='SYN')
    SYN_ACK = Constant(intValue=1, strValue='SYN-ACK')
    ACK = Constant(intValue=2, strValue='ACK')
    RIP = Constant(intValue=3, strValue='RIP')
    RIP_ACK = Constant(intValue=4, strValue='RIP-ACK')
    DATA = Constant(intValue=5, strValue='DATA')

    PACKET_TYPES = [SYN, SYN_ACK, ACK, RIP_ACK, DATA]

    def updateSeqAcknumber(self, seq, ack):
        self.SequenceNumber = seq
        self.Acknowledgement = ack

    def calculateChecksum(self):
        original_checksum = self.Checksum
        self.Checksum = 0
        bytes = self.__serialize__()
        self.Checksum = original_checksum
        return zlib.adler32(bytes) & 0xffff

    def updateChecksum(self):
        self.Checksum = self.calculateChecksum()

    def verifyChecksum(self):
        return self.Checksum == self.calculateChecksum()

    def __lt__(self, other):
        return self.SequenceNumber < other.SequenceNumber

    @classmethod
    def Create_SYN(cls):
        seq_number = random.randint(0, 2**16)
        packet = cls(Type=cls.SYN, SequenceNumber=seq_number, Checksum=0)
        packet.updateChecksum()
        return packet

    @classmethod
    def Create_SYN_ACK(cls, client_seq_num):
        seq_number = random.randint(0, 2**16)
        packet = cls(Type=cls.SYN_ACK, SequenceNumber=seq_number, Checksum=0, Acknowledgement=client_seq_num+1)
        packet.updateChecksum()
        return packet

    @classmethod
    def Create_handshake_ACK(cls, server_seq_num, client_seq_num):
        packet = cls(Type=cls.ACK, SequenceNumber=client_seq_num+1, Checksum=0, Acknowledgement=server_seq_num+1)
        packet.updateChecksum()
        return packet

    @classmethod
    def Create_packet_ACK(cls, expected_seq_number):
        packet = cls(Type=cls.ACK, Checksum=0, Acknowledgement=expected_seq_number)
        packet.updateChecksum()
        return packet

    @classmethod
    def Create_RIP(cls, expected_seq_number):
        packet = cls(Type=cls.RIP, SequenceNumber=expected_seq_number, Checksum=0)
        packet.updateChecksum()
        return packet

    @classmethod
    def Create_RIP_ACK(cls, expected_seq_num, sender_seq_num):
        packet = cls(Type=cls.RIP_ACK, SequenceNumber=expected_seq_num ,Checksum=0, Acknowledgement=sender_seq_num+1)
        packet.updateChecksum()
        return packet

    @classmethod
    def Create_DATA(cls, seq_number, data, size_for_previous_data):
        packet = cls(Type=cls.DATA, SequenceNumber=seq_number+size_for_previous_data, Checksum=0, Data=data)
        packet.updateChecksum()
        return packet

    @classmethod
    def makeSynPacket(cls, seq):
        pkt = cls()
        pkt.Type = cls.TYPE_SYN
        pkt.SequenceNumber = seq
        pkt.updateChecksum()
        return pkt

    @classmethod
    def makeSynAckPacket(cls, seq, ack):
        pkt = cls()
        pkt.Type = cls.TYPE_SYN_ACK
        pkt.SequenceNumber = seq
        pkt.Acknowledgement = ack
        pkt.updateChecksum()
        return pkt

    @classmethod
    def makeAckPacket(cls, seq, ack):
        pkt = cls()
        pkt.Type = cls.TYPE_ACK
        if seq:
            pkt.SequenceNumber = seq
        pkt.Acknowledgement = ack
        pkt.updateChecksum()
        return pkt

    @classmethod
    def makeRipPacket(cls, seq, ack):
        pkt = cls()
        pkt.Type = cls.TYPE_RIP
        pkt.SequenceNumber = seq
        pkt.Acknowledgement = ack
        pkt.updateChecksum()
        return pkt

    @classmethod
    def makeRipAckPacket(cls, ack):
        pkt = cls()
        pkt.Type = cls.TYPE_RIP_ACK
        pkt.Acknowledgement = ack
        pkt.updateChecksum()
        return pkt

    @classmethod
    def makeDataPacket(cls, seq, data):
        pkt = cls()
        pkt.Type = cls.TYPE_DATA
        pkt.SequenceNumber = seq
        pkt.Data = data
        pkt.updateChecksum()
        return pkt

