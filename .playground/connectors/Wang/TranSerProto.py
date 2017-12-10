'''
Created on 20170926

@author: teamwork 
'''
from playground.network.packet import PacketType
from playground.network.packet.fieldtypes import UINT32, STRING, BUFFER, BOOL
from playground.network.common import StackingProtocol
from playground.network.common import StackingProtocolFactory
from playground.network.common import StackingTransport
from asyncio import *
from .HandShakePacket import *
import playground
import random
import time
#from mypacket import *
from .myTransport import TranTransport
'''
    State machine:
    1. state = 0  Inactivate && waiting for Syn packet
    2. state = 1  Syn-ack sent waiting for ack
    3. state = 2  ack received connection made
    4. state = 3  rip received && ack sent!
    5. state = 4  rip sent waiting for ack
    
'''


class TranSerProto(StackingProtocol):
    def __init__(self):
        self.data = b""
        self.transport = None
        self.window = []
        self.loop = get_event_loop()
        self.higherTransport = None
        self.Status = 0
        self.RecSeq = 0
        self.SenSeq = 0
        self.deserializer = PEEPPacket.Deserializer()
        self.resentFlag = False
        self.sentCount = 0
        self.initCount = 3
        self.expectSeq =0
        self.randSeq = random.randint(0, 1000)

    def connection_made(self, transport):
        print("Server: TranSerProto Connection made!")
        self.transport = transport
        self.higherTransport = TranTransport(self.transport,self)

    def data_received(self, data):
        #self.data = data
        self.deserializer.update(data)

        for pkg in self.deserializer.nextPackets():
            if self.Status == 0:
                if pkg.Type == 0:
                    if not pkg.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    print("Server: SYN received!")
                    self.RecSeq = pkg.SequenceNumber
                    tmpkg = PEEPPacket()
                    tmpkg.Type = 1
                    tmpkg.Checksum = 0
                    tmpkg.SequenceNumber = self.randSeq
                    self.SenSeq = tmpkg.SequenceNumber
                    tmpkg.Acknowledgement = self.RecSeq + 1
                    tmpkg.updateChecksum()
                    print("Server: Ack+Syn sent!")
                    self.transport.write(tmpkg.__serialize__())
                    
                    
                if pkg.Type == 2:
                    self.Status = 1
            if self.Status == 1:
                if pkg.Type == 2:
                    if not pkg.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    print("Server: ACK received!")
                    if pkg.Acknowledgement == self.SenSeq + 1:
                        self.RecSeq = pkg.SequenceNumber
                        self.Status = 2
                        #self.SenSeq = pkg.Acknowledgement
                        print("Server: Activated!")
                        self.higherProtocol().connection_made(self.higherTransport)
                        self.sentpackets()
                        
                    
            elif self.Status == 2:
                
                    
                ''' Close the connection!'''
                if pkg.Type == 2:
                    #print("Server: Ack Packet acknowledgement number: ", pkg.Acknowledgement)
                    if not pkg.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    '''
                    if len(pkg.Data) != 0:
                        self.higherProtocol().data_received(pkg.Data)                                                                                                                                                     
                        self.RecSeq+=1
                        dataAck = PEEPPacket()
                        dataAck.Type = 2
                        dataAck.Checksum = 0
                        dataAck.SequenceNumber =0
                        dataAck.Acknowledgement = pkg.SequenceNumber + len(pkg.Data)
                        dataAck.updateChecksum()
                        self.transport.write(dataAck.__serialize__())
                    '''
                    self.window.append(pkg.Acknowledgement)
                
                if pkg.Type == 5:
                    if self.expectSeq == 0:
                        self.expectSeq = pkg.SequenceNumber
                    #print("Server: Data packets Sequence Number:", pkg.SequenceNumber)
                    if self.expectSeq == pkg.SequenceNumber:
                        if not pkg.verifyChecksum():
                            print("Required resent packet because of checksum error!")
                        self.higherProtocol().data_received(pkg.Data)                                                                                                                                           
                        dataAck = PEEPPacket()
                        dataAck.Type = 2
                        dataAck.Checksum = 0
                        dataAck.SequenceNumber = 0
                        dataAck.Data = b""
                        #dataAck.Acknowledgement = 0
                        dataAck.Acknowledgement = pkg.SequenceNumber + len(pkg.Data)
                        dataAck.updateChecksum()
                        self.transport.write(dataAck.__serialize__())
                        self.expectSeq = dataAck.Acknowledgement
                    else:
                        dataAck = PEEPPacket()
                        dataAck.Type = 2
                        dataAck.Checksum = 0
                        dataAck.SequenceNumber = 0
                        dataAck.Data = b""
                        dataAck.Acknowledgement = self.expectSeq
                        #dataAck.Acknowledgement = pkg.SequenceNumber + len(pkg.Data)
                        dataAck.updateChecksum()
                        self.transport.write(dataAck.__serialize__())
                if pkg.Type == 3:
                    if not pkg.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    print("Server: Rip received from Client!")
                    self.RecSeq = pkg.SequenceNumber
                    ServerRipAckPacket = PEEPPacket()
                    ServerRipAckPacket.Type = 4
                    self.RecSeq += 1
                    ServerRipAckPacket.Acknowledgement = self.RecSeq
                    self.SenSeq += 1
                    ServerRipAckPacket.SequenceNumber = self.SenSeq
                    self.Status = "HalfActivated"
                    ServerRipAckPacket.Checksum = 0
                    ServerRipAckPacket.updateChecksum()
                    self.transport.write(ServerRipAckPacket.__serialize__())
                    self.connection_lost("client request")
                    '''
                        Only transfer data in the buffer!
                        Waiting for the transportation complete!
                    '''
            if self.Status ==3:
                if pkg.Type == 4:
                    if not pkg.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    print("Server: Rip-Ack received!")
                    self.Status = 0
                    self.connection_lost("server request")
                    
    def sentpackets(self):
        if len(self.data)!=0:
            self.higherTransport.sent(self.data)
            #print("sent")
        self.loop.call_later(0.5,self.sentpackets)
    

    def connection_lost(self, exc):
        self.higherProtocol().connection_lost(exc)
        self.higherTransport().lowerTransport().close()
        print('Connection stopped because {}'.format(exc))
