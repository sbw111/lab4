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
import .HandShakePacket
from .TranSerProto import *
from .ServerPassThrough import *
from .ServerAppProtocol import *
from asyncio import *


if __name__=='__main__':
    loop = get_event_loop()
    f = StackingProtocolFactory(lambda: ServerPassThrough(), lambda: TranSerProto())
    ptConnector = playground.Connector(protocolStack=f)
    playground.setConnector('ServerStack', ptConnector)
    coro = playground.getConnector('ServerStack').create_playground_server(lambda:ServerAppProtocol(),8998)
    myserver= loop.run_until_complete(coro)
    loop.run_forever()
    myserver.close()
    loop.close()
