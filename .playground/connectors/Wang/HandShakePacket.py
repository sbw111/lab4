'''
Created on 20170926

@author: wangweizhou
'''

from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT32, UINT8, UINT16, BUFFER,STRING
from playground.network.packet.fieldtypes.attributes import Optional
import zlib

'''
    PType: record packet type:
    PType==0    SYN packet
    PType==1    SYN&ACK packet
    PType==2    ACK packet
    PType==3    RIP
    PType==4    RIP-ACK
    PType==5    Data
    Seq: store SYN sequential number
    Ack: store Ack sequential number which should be (syn+1)
'''


class PEEPPacket(PacketType):
    DEFINITION_IDENTIFIER = "HandshakePacket"
    DEFINITION_VERSION = "1.0"
    FIELDS = [("Type", UINT8),
              ("SequenceNumber", UINT32({Optional: True})),
              ("Acknowledgement", UINT32({Optional: True})),
              ("Checksum", UINT16),
              ("Data", BUFFER({Optional: True}))]

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
