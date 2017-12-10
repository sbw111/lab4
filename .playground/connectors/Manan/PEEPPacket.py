import playground
import zlib
from playground.common import CustomConstant as Constant
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT8, UINT32, UINT16, BUFFER
from playground.network.packet.fieldtypes.attributes.Descriptor import Optional


class PEEPPacket(PacketType):
    DEFINITION_IDENTIFIER = 'PEEP.Packet'
    DEFINITION_VERSION = '1.0'

    FIELDS = [
        ('Type', UINT8),
        ('SequenceNumber', UINT32({Optional: True})),
        ('Checksum', UINT16),
        ("Acknowledgement", UINT32({Optional: True})),
        ("Data", BUFFER({Optional: True}))
    ]

    SYN = Constant(intValue=0, strValue="SYN")
    SYN_ACK = Constant(intValue=1, strValue="SYN-ACK")
    ACK = Constant(intValue=2, strValue="ACK")
    RIP = Constant(intValue=3, strValue="RIP")
    RIP_ACK = Constant(intValue=4, strValue="RIP-ACK")
    RST = Constant(intValue=5, strValue="RST")
    DATA = Constant(intValue=6, strValue="DATA")

    PACKET_TYPES = [SYN, SYN_ACK, ACK, RIP, RIP_ACK, RST, DATA]

    def calculate_checksum(self):
        original_checksum = self.Checksum
        self.Checksum = 0
        bytes = self.__serialize__()
        self.Checksum = original_checksum
        return zlib.adler32(bytes) & 0xffff

    def update_checksum(self):
        self.Checksum = self.calculate_checksum()

    def verify_checksum(self):
        return self.Checksum == self.calculate_checksum()

