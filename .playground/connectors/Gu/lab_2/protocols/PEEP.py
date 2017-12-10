import asyncio, heapq
from playground.network.common import StackingProtocol

from ..constants import DATA_FIELD_SIZE, BASIC_TIMEOUT, TERMINATION_TIMEOUT, WINDOW
from ...playgroundpackets import *

class PEEP(StackingProtocol):

    def __init__(self):
        super(PEEP, self).__init__()
        # transport
        self.transport = None
        # deserializer
        self._deserializer = PEEPPacket.Deserializer()
        # state
        self._state = 0
        # flag packet check
        self._need_flag_packet_resent = [True, True, True, True]
        # seq num
        self._seq_num_for_handshake = None
        self._seq_num_for_last_packet = None
        self._seq_num_for_next_expected_packet = None
        # heap
        self._retransmission_heap = []
        self._disordered_packets_heap = []
        # size
        self._size_for_last_packet = 1
        # backlog
        self._backlog_buffer = b''
        # rip state
        self._rip_sent = False
        self._need_rip_resent = True
        # rip ack state
        self._rip_ack_sent = False
        # termination
        self._termination_handler = None

    def ack_received(self, ack_packet):
        print('received ack packet with ack %s' % ack_packet.Acknowledgement)
        if ack_packet.verifyChecksum():
            while len(self._retransmission_heap) > 0 and self._retransmission_heap[0].SequenceNumber < ack_packet.Acknowledgement:
                packet_for_removing = heapq.heappop(self._retransmission_heap)
                print('remove packet from retransmission heap with seq num %s' % packet_for_removing.SequenceNumber)
                if len(self._backlog_buffer) > 0:
                    chunk, self._backlog_buffer = self._backlog_buffer[:DATA_FIELD_SIZE], self._backlog_buffer[DATA_FIELD_SIZE:]
                    data_packet_for_backlog = PEEPPacket.Create_DATA(self._seq_num_for_last_packet, chunk, self._size_for_last_packet)
                    self.transport.write(data_packet_for_backlog.__serialize__())
                    print('sent a data packet from backlog with seq num %s' % data_packet_for_backlog.SequenceNumber)
                    heapq.heappush(self._retransmission_heap, data_packet_for_backlog)
                    asyncio.get_event_loop().call_later(BASIC_TIMEOUT, self.check_retransmission_heap, data_packet_for_backlog.SequenceNumber)
                    self._seq_num_for_last_packet = data_packet_for_backlog.SequenceNumber
                    self._size_for_last_packet = len(chunk)
        else:
            print('received a ack packet with incorrect checksum')

    def data_packet_received(self, data_packet):
        print('received data packet with seq num %s' % data_packet.SequenceNumber)
        if data_packet.verifyChecksum():

            if data_packet.SequenceNumber == self._seq_num_for_next_expected_packet:
                # ------ higher protocol data received ------
                self.higherProtocol().data_received(data_packet.Data)
                # -------------------------------------------
                self._seq_num_for_next_expected_packet += len(data_packet.Data)
                # check disordered packets heap whether there exists extra packets can be transmitted
                while len(self._disordered_packets_heap) > 0 and self._disordered_packets_heap[0].SequenceNumber == self._seq_num_for_next_expected_packet:
                    next_packet = heapq.heappop(self._disordered_packets_heap)
                    self.higherProtocol().data_received(next_packet.Data)
                    self._seq_num_for_next_expected_packet += len(next_packet.Data)

            else:
                if data_packet not in self._disordered_packets_heap:
                    heapq.heappush(self._disordered_packets_heap, data_packet)
        else:
            print('received a data packet with incorrect checksum')
        # ------ send ack ------
        ack_packet = PEEPPacket.Create_packet_ACK(self._seq_num_for_next_expected_packet)
        self.transport.write(ack_packet.__serialize__())
        print('send ack packet with ack %s' % ack_packet.Acknowledgement)
        # ----------------------

    def rip_received(self, rip_packet):
        if rip_packet.verifyChecksum():
            if rip_packet.SequenceNumber == self._seq_num_for_next_expected_packet:
                self._seq_num_for_next_expected_packet += 1
                rip_ack_packet = PEEPPacket.Create_RIP_ACK(self._seq_num_for_last_packet + self._size_for_last_packet, self._seq_num_for_next_expected_packet)
                self.transport.write(rip_ack_packet.__serialize__())
                self._need_flag_packet_resent[-1] = False
                self.transport.close()
                self._state = -1
            else:
                print('received a rip packet with wrong sequence')
        else:
            print('received a rip packet with incorrect checksum')

    def rip_ack_received(self, rip_ack_packet):
        if rip_ack_packet.verifyChecksum():
            if rip_ack_packet.SequenceNumber == self._seq_num_for_next_expected_packet:
                self._seq_num_for_next_expected_packet += 1
                self._termination_handler.cancel()
                self._need_flag_packet_resent[-1] = False
                self.transport.close()
                self._state = -1
            else:
                print('received a rip-ack packet with wrong sequence')
        else:
            print('received a rip-ack packet with incorrect checksum')

    def process_data(self, data_buffer):
        if len(self._backlog_buffer) > 0:
            self._backlog_buffer += data_buffer
        else:
            while len(data_buffer) > 0 and len(self._retransmission_heap) < WINDOW:
                chunk, data_buffer = data_buffer[:DATA_FIELD_SIZE], data_buffer[DATA_FIELD_SIZE:]
                data_chunk_packet = PEEPPacket.Create_DATA(self._seq_num_for_last_packet or self._seq_num_for_handshake, chunk, self._size_for_last_packet)
                # ------ transport write ------
                self.transport.write(data_chunk_packet.__serialize__())
                print('sent a data packet with seq num %s' % data_chunk_packet.SequenceNumber)
                # -----------------------------
                heapq.heappush(self._retransmission_heap, data_chunk_packet)
                # ------ check if retransmission heap does not pop the packet after timeout ------
                asyncio.get_event_loop().call_later(BASIC_TIMEOUT, self.check_retransmission_heap, data_chunk_packet.SequenceNumber)
                # --------------------------------------------------------------------------------
                self._seq_num_for_last_packet = data_chunk_packet.SequenceNumber
                self._size_for_last_packet = len(chunk)

            if len(data_buffer) > 0:
                self._backlog_buffer += data_buffer
                print('backlog buffer length is %s' % len(self._backlog_buffer))

    def resend_packet(self, packet):
        self.transport.write(packet.__serialize__())
        print('resent a data packet with seq num %s' % packet.SequenceNumber)
        asyncio.get_event_loop().call_later(BASIC_TIMEOUT, self.check_retransmission_heap, packet.SequenceNumber)

    def check_flag_packet(self, flag_packet):
        if self._need_flag_packet_resent[flag_packet.Type]:
            self.transport.write(flag_packet.__serialize__())
            asyncio.get_event_loop().call_later(BASIC_TIMEOUT, self.check_flag_packet, flag_packet)

    def check_retransmission_heap(self, seq_num):
        for packet in self._retransmission_heap:
            if packet.SequenceNumber == seq_num:
                self.transport.write(packet.__serialize__())
                print('resent a data packet with seq num %s' % packet.SequenceNumber)
                asyncio.get_event_loop().call_later(BASIC_TIMEOUT, self.check_retransmission_heap, packet.SequenceNumber)
                break

    def end_session(self):
        if len(self._backlog_buffer) == 0 and len(self._retransmission_heap) == 0:
            rip_packet = PEEPPacket.Create_RIP((self._seq_num_for_last_packet or self._seq_num_for_handshake) + self._size_for_last_packet)
            self.transport.write(rip_packet.__serialize__())
            asyncio.get_event_loop().call_later(BASIC_TIMEOUT, self.check_flag_packet, rip_packet)
            self._termination_handler = asyncio.get_event_loop().call_later(TERMINATION_TIMEOUT, self.timeout_close)
            self._rip_sent = True
            self._seq_num_for_last_packet = rip_packet.SequenceNumber
            self._size_for_last_packet = 1
        else:
            asyncio.get_event_loop().call_later(BASIC_TIMEOUT, self.end_session)

    def timeout_close(self):
        if self._state != -1:
            self.transport.close()
            self._state = -1

'''
    old implementation for session end 
    
    ====================================================================================================================
    
    def check_rip(self, rip_packet):
        if self._need_rip_resent:
            self.transport.write(rip_packet.__serialize__())
            asyncio.get_event_loop().call_later(BASIC_TIMEOUT, self.check_rip, rip_packet)

    def clean_buffer(self):
        if len(self._backlog_buffer) == 0 and len(self._retransmission_heap) == 0:
            rip_packet = PEEPPacket.Create_RIP(self._seq_num_for_last_packet + self._size_for_last_packet)
            self.transport.write(rip_packet.__serialize__())
            asyncio.get_event_loop().call_later(BASIC_TIMEOUT, self.check_rip, rip_packet)
            self._seq_num_for_last_packet = rip_packet.SequenceNumber
            self._size_for_last_packet = 1
            asyncio.get_event_loop().call_later(BASIC_TIMEOUT * 2, self.timeout_close)
        else:
            asyncio.get_event_loop().call_later(BASIC_TIMEOUT, self.clean_buffer)

    def rip_received(self, rip_packet):
        if rip_packet.verifyChecksum():
            if rip_packet.SequenceNumber == self._seq_num_for_next_expected_packet:
                self._seq_num_for_next_expected_packet += 1
                rip_ack_packet = PEEPPacket.Create_RIP_ACK(self._seq_num_for_last_packet + self._size_for_last_packet, self._seq_num_for_next_expected_packet)
                self.transport.write(rip_ack_packet.__serialize__())
                self._rip_ack_sent = True
                if self._rip_sent:
                    self.transport.close()
                    self._state = -1
                else:
                    self.clean_buffer()
            else:
                print('received a rip packet with wrong sequence')
        else:
            print('received a rip packet with incorrect checksum')
            
    def rip_ack_received(self, rip_ack_packet):
        if rip_ack_packet.verifyChecksum():
            if rip_ack_packet.SequenceNumber == self._seq_num_for_next_expected_packet:
                self._seq_num_for_next_expected_packet += 1
                if self._rip_ack_sent:
                    self.transport.close()
                    self._state = -1
                else:
                    self._need_rip_resent = False
            else:
                print('received a rip-ack packet with wrong sequence')
        else:
            print('received a rip-ack packet with incorrect checksum')
    
    ====================================================================================================================
'''
