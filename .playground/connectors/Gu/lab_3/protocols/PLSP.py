import random, hashlib

from playground.network.common import StackingProtocol

from ...playgroundpackets.PLSPacket import PLSPacket, PlsHello, PlsKeyExchange, PlsHandshakeDone, PlsData, PlsClose
from ..factory.CertFactory import CertFactory
from ..transport.PLSTransport import PLSTransport
from ..utils.CryptoUtil import CryptoUtil

class PLSP(StackingProtocol):

    def __init__(self):
        super(PLSP, self).__init__()
        # variables for transport
        self.transport = None
        self._deserializer = PLSPacket.Deserializer()
        # cert factory and cert vars
        self.cf = CertFactory()
        self._private_key = self.cf.getPrivateKeyForAddr('bb8_prik.pem')
        # self._public_key = self.cf.getPublicKeyForAddr('bb8_pubk.pem')
        self._pubk_for_other_side = None
        self._pre_key = None
        self._pre_key_for_other_side = None
        self._certs = []
        self._certs_for_other_side = None
        self._certs.append(self.cf.getCertsForAddr('bb8.csr'))
        # vars for handshake
        self._nonce = None
        self._nonce_for_other_side = None
        self._state = 0
        self._messages_for_handshake = []
        self._hash_for_handshake = None

    def data_received(self, data):
        self._deserializer.update(data)
        for packet in self._deserializer.nextPackets():
            if isinstance(packet, PlsData):
                self.higherProtocol().data_received(packet.Ciphertext)
            elif isinstance(packet, PlsHello):
                '''
                1. store certs from the other side (?)
                2. get the other side's pubk from the certs
                3. store the other side's nonce
                4. store this message for SHA1
                '''
                self._certs_for_other_side = list(packet.Certs)
                self._nonce_for_other_side = packet.Nonce
                self._pubk_for_other_side = self.cf.getPubkFromCert(packet.Certs[0])
                self._messages_for_handshake.append(packet.__serialize__())
                if self._state == 0:
                    # start to send plshello
                    self._nonce = random.randint(0, 2 ** 64)
                    pls_hello = PlsHello(Nonce=self._nonce, Certs=self._certs)
                    pls_hello_bytes = pls_hello.__serialize__()
                    self.transport.write(pls_hello_bytes)
                    # print('pls server sent plshello')
                    self._state = 2
                    self._messages_for_handshake.append(pls_hello_bytes)
                elif self._state == 1:
                    self._pre_key = self.cf.getPreKey()
                    pls_key_exchange = PlsKeyExchange(PreKey=CryptoUtil.RSAEncrypt(self._pubk_for_other_side, self._pre_key), NoncePlusOne=self._nonce_for_other_side + 1)
                    pls_key_exchange_bytes = pls_key_exchange.__serialize__()
                    self.transport.write(pls_key_exchange_bytes)
                    # print('pls client sent plskeyexchange')
                    self._state = 3
                    self._messages_for_handshake.append((pls_key_exchange_bytes))
                else:
                    raise ValueError
            elif isinstance(packet, PlsKeyExchange):
                if packet.NoncePlusOne == self._nonce + 1:
                    self._pre_key_for_other_side = CryptoUtil.RSADecrypt(self._private_key, packet.PreKey)
                    self._messages_for_handshake.append(packet.__serialize__())
                    if self._state == 2:
                        self._pre_key = self.cf.getPreKey()
                        pls_key_exchange = PlsKeyExchange(PreKey=CryptoUtil.RSAEncrypt(self._pubk_for_other_side, self._pre_key), NoncePlusOne=self._nonce_for_other_side + 1)
                        pls_key_exchange_bytes = pls_key_exchange.__serialize__()
                        self.transport.write(pls_key_exchange_bytes)
                        # print('pls server sent plskeyexchange')
                        self._state = 4
                        self._messages_for_handshake.append(pls_key_exchange_bytes)
                    elif self._state == 3:
                        m = hashlib.sha1()
                        m.update(self._messages_for_handshake[0] + self._messages_for_handshake[1] + self._messages_for_handshake[2] + self._messages_for_handshake[3])
                        self._hash_for_handshake = m.digest()
                        pls_handshake_done = PlsHandshakeDone(ValidationHash=self._hash_for_handshake)
                        self.transport.write(pls_handshake_done.__serialize__())
                        # print('pls client sent plshandshakedone')
                        self._state = 5
                    else:
                        raise ValueError
                else:
                    raise ValueError
            elif isinstance(packet, PlsHandshakeDone):
                validation_hash = packet.ValidationHash
                if self._state == 4:
                    m = hashlib.sha1()
                    m.update(self._messages_for_handshake[0] + self._messages_for_handshake[1] +
                             self._messages_for_handshake[2] + self._messages_for_handshake[3])
                    self._hash_for_handshake = m.digest()
                    if self._hash_for_handshake == validation_hash:
                        pls_handshake_done = PlsHandshakeDone(ValidationHash=self._hash_for_handshake)
                        self.transport.write(pls_handshake_done.__serialize__())
                        self._state = 6
                        # ------------ connect to higher protocol ------------
                        self.higherProtocol().connection_made(PLSTransport(self.transport, self))
                    else:
                        raise ValueError
                elif self._state == 5:
                    if self._hash_for_handshake == validation_hash:
                        self.higherProtocol().connection_made(PLSTransport(self.transport, self))
                        self._state = 6
                else:
                    raise ValueError
            elif isinstance(packet, PlsClose):
                raise NotImplementedError
            else:
                print('PLSP is waiting for a PLS packet.')

    def process_data(self, data):
        pls_data = PlsData(Ciphertext=data, Mac=b'')
        self.transport.write(pls_data.__serialize__())