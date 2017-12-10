import zlib
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT8, UINT16, UINT32, UINT64,\
    STRING, BUFFER, BOOL, ComplexFieldType, PacketFields
from playground.network.packet.fieldtypes.attributes import Optional


class PEEPPacket(PacketType):
    DEFINITION_IDENTIFIER = "PEEP.Packet"
    DEFINITION_VERSION = "1.0"

    SYN = 0
    SYNACK = 1
    ACK = 2
    RIP = 3
    RIPACK = 4
    DATA = 5

    FIELDS = [
        ("Type", UINT8),
        ("SequenceNumber", UINT32({Optional: True})),
        ("Checksum", UINT16),
        ("Acknowledgement", UINT32({Optional: True})),
        ("Data", BUFFER({Optional: True}))
    ]

    def calculateChecksum(self):
        oldChecksum = self.Checksum
        self.Checksum = 0
        bytes = self.__serialize__()
        self.Checksum = oldChecksum
        return zlib.adler32(bytes) & 0xffff

    def updateChecksum(self):
        self.Checksum = self.calculateChecksum()

    def verifyChecksum(self):
        return self.Checksum == self.calculateChecksum()

    def __repr__(self):
        return "PEEPPacket: \n" + "Type: " + str(self.Type) + "\nSeq: " + str(self.SequenceNumber) + "\nAck: " + str(self.Acknowledgement)
