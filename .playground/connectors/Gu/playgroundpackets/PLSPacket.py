from playground.network.packet.fieldtypes.attributes import Optional
from playground.network.packet.fieldtypes import UINT64, BUFFER, STRING, LIST
from playground.network.packet import PacketType
# from playground.common import CustomConstant as Constant


class PLSPacket(PacketType):
    DEFINITION_IDENTIFIER = 'netsecfall2017.pls.basepacket'
    DEFINITION_VERSION = '1.0'

class PlsHello(PLSPacket):
    DEFINITION_IDENTIFIER = 'netsecfall2017.pls.hello'
    DEFINITION_VERSION = '1.0'
    FIELDS = [
        ('Nonce', UINT64),
        ('Certs', LIST(BUFFER))
    ]

class PlsKeyExchange(PLSPacket):
    DEFINITION_IDENTIFIER = 'netsecfall2017.pls.keyexchange'
    DEFINITION_VERSION = '1.0'
    FIELDS = [
        ('PreKey', BUFFER),
        ('NoncePlusOne', UINT64)
    ]

class PlsHandshakeDone(PLSPacket):
    DEFINITION_IDENTIFIER = 'netsecfall2017.pls.handshakedone'
    DEFINITION_VERSION = '1.0'
    FIELDS = [
        ('ValidationHash', BUFFER)
    ]

class PlsData(PLSPacket):
    DEFINITION_IDENTIFIER = 'netsecfall2017.pls.data'
    DEFINITION_VERSION = '1.0'
    FIELDS = [
        ('Ciphertext', BUFFER),
        ('Mac', BUFFER)
    ]

class PlsClose(PLSPacket):
    DEFINITION_IDENTIFIER = 'netsecfall2017.pls.close'
    DEFINITION_VERSION = '1.0'
    FIELDS = [
        ("Error", STRING({Optional: True}))
    ]

