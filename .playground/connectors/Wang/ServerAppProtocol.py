'''
Created on 2017年9月28日

@author: wangweizhou
'''
from playground.network.packet.fieldtypes import UINT32, STRING, BUFFER,BOOL,UINT8
from playground.network.packet import PacketType
import playground
from asyncio import *
from .HandShakePacket import PEEPPacket
from .AppPacket import AppPacket



class ServerAppProtocol(Protocol):
    def __init__(self):
        self.transport=None        # transport contains the data you need to transfer while connecting
        self.deserializer = PacketType.Deserializer()
        self.loop = get_event_loop()
    def connection_made(self, transport):
        print("Server: Application layer connection made! ")
        self.transport = transport
        #self.loop.call_later(5,self.echo())

    def echo(self):
        mypacket = AppPacket()
        mypacket.Message = "This is the transport layer test!1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111"
        self.transport.write(mypacket.__serialize__())
        
    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            msg = pkt.Message
            print("Server:"+msg)
            self.loop.call_later(1,self.echo)
            #self.echo()
            
        

    def connection_lost(self, exc):
        print('Connection stopped because {}'.format(exc))



