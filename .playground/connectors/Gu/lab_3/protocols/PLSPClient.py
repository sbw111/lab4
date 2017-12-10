import random
from .PLSP import PLSP
from ...playgroundpackets.PLSPacket import PlsHello


class PLSPClient(PLSP):

    def __init__(self):
        super(PLSPClient, self).__init__()

    def connection_made(self, transport):
        self.transport = transport
        # start to handshake
        self._nonce = random.randint(0, 2**64)
        pls_hello = PlsHello(Nonce=self._nonce, Certs=self._certs)
        pls_hello_bytes = pls_hello.__serialize__()
        self.transport.write(pls_hello_bytes)
        # print('pls client send plshello')
        self._state = 1
        self._messages_for_handshake.append(pls_hello_bytes)

    def connection_lost(self, exc):
        self.higherProtocol().connection_lost(exc)