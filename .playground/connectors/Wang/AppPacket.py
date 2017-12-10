'''
Created on 2017年10月6日

@author: wangweizhou
'''
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT32, UINT8, UINT16, BUFFER,STRING
from playground.network.packet.fieldtypes.attributes import Optional
import zlib

class AppPacket(PacketType):
    DEFINITION_IDENTIFIER = "ApplicationPacket"
    DEFINITION_VERSION = "1.0"
    FIELDS = [("Message", STRING)]