from asyncio import *
import playground
from .HandShakePacket import *
from playground.network.packet import PacketType
from playground.network.common import PlaygroundAddress
from playground.network.common import StackingProtocolFactory
from playground.network.common import StackingProtocol
from playground.network.common import StackingTransport
from .myTransport import TranTransport
import random
import time
import logging
#from asyncio.windows_events import NULL


'''
State machine definition:
Client:
    state = 0 Inactivated 
    state = 1 Waiting for SYN-Ack
    state = 2 Ack sent && Connection made 
    state = 3 Rip sent waiting for ack
    state = 4 ack receive waiting for Rip
'''

logging.getLogger().setLevel(logging.NOTSET)  # this logs *everything*
logging.getLogger().addHandler(logging.StreamHandler())  # logs to stderr

class TranCliProto(StackingProtocol):
    def __init__(self):
        self.data = b""
        self.loop = get_event_loop()
        self.transport = None
        self.Status = 0
        self.RecSeq = 0
        self.SenSeq = 0
        self.higherTransport = None
        self.window = []
        self.deserializer = PEEPPacket.Deserializer()
        self.expectSeq = 0
        self.sentCount = 0
        self.initCount = 3
        self.resentFlag = False
        self.randomSeq = random.randint(0, 1000)
        
    def connection_made(self, transport):
        print("Client: TranCliProto Connection made")
        self.transport = transport
        self.higherTransport = TranTransport(self.transport,self)
        
        self.connection_request()
        self.Status = 1

    def data_received(self, data):
        self.deserializer.update(data)
        for pkt in self.deserializer.nextPackets():
            if self.Status == 1:
                if pkt.Type == 1 and pkt.Acknowledgement == self.SenSeq:
                    
                    self.resentFlag = False  #init resent flag
                    if not pkt.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    print("Client: Ack+Syn received!")
                    self.RecSeq = pkt.SequenceNumber
                    AckPkt = PEEPPacket()
                    AckPkt.Type = 2
                    AckPkt.Checksum = 0
                    AckPkt.SequenceNumber = self.SenSeq
                    
                    AckPkt.Acknowledgement = self.RecSeq + 1
                    self.RecSeq=AckPkt.Acknowledgement
                    AckPkt.updateChecksum()
                    self.transport.write(AckPkt.__serialize__())
                    self.Status = 2
                    print("Client: Ack sent!")
                    self.higherProtocol().connection_made(self.higherTransport)
                    self.sentpackets()
                    #self.loop.call_later(0.5,self.initResent)
                    #self.loop.call_later(0.5,self.higherConnectionmade,AckPkt)
                    


            if self.Status == 2:
                
                
                if pkt.Type == 2:
                    
                    if not pkt.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    print("Client: Ack Packet acknowledgement number: ", pkt.Acknowledgement)
                    '''
                    if pkt.Data != None:
                        self.higherProtocol().data_received(pkt.Data)                                                                                                                                                     
                        self.RecSeq+=1
                        dataAck = PEEPPacket()
                        dataAck.Type = 2
                        dataAck.Checksum = 0
                        dataAck.SequenceNumber =0
                        dataAck.Acknowledgement = pkt.SequenceNumber + len(pkt.Data)
                        dataAck.updateChecksum()
                        self.transport.write(dataAck.__serialize__())
                    '''
                    
                    self.window.append(pkt.Acknowledgement)
                    
                if pkt.Type == 5:
                    if self.expectSeq == 0:
                        self.expectSeq = pkt.SequenceNumber
                    print("expectSeq", self.expectSeq)
                    #print("Client: Data packets Sequence Number:", pkt.SequenceNumber)
                    if self.expectSeq == pkt.SequenceNumber:
                        if not pkt.verifyChecksum():
                            print("Required resent packet because of checksum error!")
                        self.higherProtocol().data_received(pkt.Data)                                                                                                                                           
                        dataAck = PEEPPacket()
                        dataAck.Type = 2
                        dataAck.Checksum = 0
                        dataAck.SequenceNumber = 0
                        dataAck.Data = b""
                        dataAck.Acknowledgement = pkt.SequenceNumber + len(pkt.Data)
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
                        dataAck.updateChecksum()
                        self.transport.write(dataAck.__serialize__())
                    
                if pkt.Type == 3:
                    if not pkt.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    print("Server: Rip received from Client!")
                    self.RecSeq = pkt.SequenceNumber
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
                if pkt.Type == 4:
                    if not pkt.verifyChecksum():
                        print("Required resent packet because of checksum error!")
                    print("Server: Rip-Ack received!")
                    self.Status = 0
                    self.connection_lost("client request")
                

    def connection_request(self):
        handshakeRequest = PEEPPacket()
        handshakeRequest.Type = 0
        handshakeRequest.Acknowledgement = 0
        handshakeRequest.SequenceNumber =  self.randomSeq # currently the range is [0,99]
        handshakeRequest.Checksum = 0  # have to be improved in the future
        handshakeRequest.updateChecksum()
        self.SenSeq = self.randomSeq+1
        print("Client: Connection Request sent! Sequence Number:", handshakeRequest.SequenceNumber)
        #self.transport.write(handshakeRequest.__serialize__())
        self.initResent()
        self.resentHandshake(handshakeRequest)
    
    def sentpackets(self):
        if len(self.data)!=0:
            self.higherTransport.sent(self.data)
            #print("sent")
        self.loop.call_later(0.5,self.sentpackets)
    def resentHandshake(self,pkg):
        if self.sentCount > 0 and self.resentFlag == True:
            self.sentCount = self.sentCount-1
            #print("Resent packet type:", pkg.Type)
            self.transport.write(pkg.__serialize__())
            self.loop.call_later(0.5,self.resentHandshake, pkg)
        elif self.sentCount<=0:
            self.connection_lost("Timeout")
            
    def higherConnectionmade(self,pkg):
        if self.sentCount > 0 and self.resentFlag == True:
            self.sentCount = self.sentCount-3
            #print("Resent packet type:", pkg.Type)
            self.transport.write(pkg.__serialize__())
            self.loop.call_later(0.5,self.higherConnectionmade, pkg)
        else:
            self.resentFlag = False
            self.Status = 2
            self.higherProtocol().connection_made(self.higherTransport)
    
    
    def initResent(self):
        self.sentCount = self.initCount
        self.resentFlag = True
    
    def close_request(self):
        '''
            Close higher level transportation!
        '''
        print("Client: Rip request sent!")
        closePacket = PEEPPacket()
        closePacket.Type = 3
        self.SenSeq += 1
        closePacket.SequenceNumber = self.SenSeq
        closePacket.Acknowledgement = 0
        closePacket.Checksum = 0
        self.Status = "HalfActivated"
        closePacket.updateChecksum()
        self.transport.write(closePacket.__serialize__())

    def connection_lost(self, exc):
        self.transport.close()
        self.higherProtocol().connection_lost(exc)
        print("Connection stop because {}".format(exc))
