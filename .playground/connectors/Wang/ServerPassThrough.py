'''
Created on 2017年9月28日

@author: wangweizhou
'''
from playground.network.packet.fieldtypes import UINT32, STRING, BUFFER,BOOL
from playground.network.packet import PacketType
from playground.network.common import StackingProtocol
from playground.network.common import StackingProtocolFactory
from playground.network.common import StackingTransport
import playground
from asyncio import *

class ServerPassThrough(StackingProtocol):
    def __init__(self):
        super().__init__
        
    def connection_made(self,transport):
        self.transport=transport
        print("Server: Passthrough Layer connected")
        higherTransport = StackingTransport(self.transport)
        self.higherProtocol().connection_made(higherTransport)
        
    def data_received(self,data):
        print("Data received by FIRST layer!")
        self.data = data
        self.higherProtocol().data_received(self.data)
    
    def connection_lost(self,exc):
        print('Connection stopped because {}'.format(exc))
        self.higherProtocol().connection_lost(exc)
        