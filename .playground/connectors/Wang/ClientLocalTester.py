'''
Created on 2017年9月27日

@author: wangweizhou
'''
from playground.network.packet.fieldtypes import UINT32, STRING, BUFFER,BOOL
from playground.network.packet import PacketType
from playground.network.common import StackingProtocol
from playground.network.common import StackingProtocolFactory
from playground.network.common import StackingTransport
import playground
from .HandShakePacket import *
from .ClientPassThrough import *
from .ClientAppProtocol import *
from asyncio import *
from .TranCliProto import TranCliProto

if __name__=='__main__':
    loop = get_event_loop()
    f = StackingProtocolFactory(lambda: ClientPassThrough(), lambda: TranCliProto())
    ptConnector = playground.Connector(protocolStack=f)
    playground.setConnector('ClientStack', ptConnector)
    connect = playground.getConnector('ClientStack').create_playground_connection (lambda:ClientAppProtocol(), '20174.1.1.1', 8998)
    mytransport, myclientprotocol = loop.run_until_complete(connect)
    #myclientprotocol.connection_made(mytransport)
    #myclientprotocol.SentRequest();
    loop.run_forever()
    loop.close()
