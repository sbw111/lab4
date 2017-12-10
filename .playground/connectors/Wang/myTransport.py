'''
Created on 2017年10月5日

@author: wangweizhou
'''
from playground.network.common import StackingTransport
from .HandShakePacket import PEEPPacket
import random
import asyncio

class TranTransport(StackingTransport):
    def __init__(self, lowerTransport, protocol):
        super().__init__(lowerTransport, extra=None)
        self._lowerTransport = lowerTransport
        self.protocol = protocol
        self.buffer = []        #Packet buffer
        self.Size = 1000
        self.windowSize = 3 * self.Size
        self.protocol.packetsize = self.Size
        self.window = []  # Sliding window: recording the sequence number of the packets that has been sent
        self.pktseqStore = []  # To store bytes that have been transmitted
        self.seqStore = []
        self.baselen = 0
        self.currentlen =0
        self.lastsize=0
        self.maxAck = 0
        

    def write(self, data):
        self.protocol.data = self.protocol.data + data
        #self.currentlen =0
        #self.seqStore=[]
        #self.protocol.window = []
        self.baselen = self.protocol.SenSeq
        
        '''
        if len(self.protocol.data)==0: 
            self.protocol.sentpackets(data)
        else:
            self.protocol.data = self.protocol.data + data
        '''
        
        
    def sent(self,data):
        if len(data)!=0:
            
            self.checkAck()
            self.baselen = self.protocol.SenSeq
            self.buffer = data
            self.buffer = self.buffer[self.currentlen:len(self.buffer)] #update the length of windows 截取buffer大小
            self.protocol.data = self.buffer  # 把update的数据传给protocol
            self.window = self.buffer[0:self.windowSize]  #截取window大小
            for i in range(0, len(self.window), self.Size):
                unit = self.buffer[i:(i+self.Size)]  #截取每个包的数据，分包
                Pkt = PEEPPacket() 
                Pkt.Type = 5  #发送data包
                Pkt.SequenceNumber = self.protocol.SenSeq #把packet sequence number赋值
                self.protocol.SenSeq = Pkt.SequenceNumber+ len(unit) # 更新sequence number ,5->15
                Pkt.Acknowledgement = 0 
                Pkt.Data = unit #把数据放入data
                #Pkt.Checksum = 0
                Pkt.updateChecksum()
                self.lowerTransport().write(Pkt.__serialize__()) 
                self.seqStore.append(self.protocol.SenSeq) 
         
    def checkAck(self): # compare acks with seqs
        self.seqStore.sort()
        self.protocol.window.sort()
        if len(self.protocol.window)!=0:
            if self.protocol.window[len(self.protocol.window)-1]>self.maxAck:
                self.maxAck = self.protocol.window[len(self.protocol.window)-1]
        else:
            self.maxAck = self.baselen
        self.protocol.SenSeq = self.maxAck
        self.currentlen = self.maxAck-self.baselen
        self.seqStore=[]
        self.protocol.window=[]
        #print("Acknowledgement Checked!")
    
            
    def clearance(self):
        while len(self.window)!=0 :
            self.window.pop()
    
    
    
    def close(self):
        print("Client: Rip request sent!")
        closePacket = PEEPPacket()
        closePacket.Type = 3
        closePacket.SequenceNumber = self.protocol.SenSeq
        closePacket.Acknowledgement = 0
        closePacket.Checksum = 0
        closePacket.updateChecksum()
        self.protocol.Status=3
        self.lowerTransport().write(closePacket.__serialize__())
        print("waiting for rip ack packet")
        self.lowerTransport().close()
    
