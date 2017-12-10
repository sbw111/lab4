import random
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

class CertFactory(object):

    def __init__(self):
        super(CertFactory, self).__init__()
        self._path_prefix = '/Users/qiyanggu/Documents/keys/netsec/'

    def getPrivateKeyForAddr(self, addr):
        return self.getContent(self._path_prefix + addr)

    def getCertsForAddr(self, addr):
        return self.getContent(self._path_prefix + addr)

    def getRootCert(self):
        return self.getContent(self._path_prefix + 'root.crt')

    def getPublicKeyForAddr(self, addr):
        return self.getContent((self._path_prefix + addr))

    def getPreKey(self):
        return str(random.randint(0, 2**16)).encode()

    def getPubkFromCert(self, cert):
        csr = x509.load_pem_x509_csr(cert, default_backend())
        return csr.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)

    @staticmethod
    def getContent(addr):
        content = b''
        with open(addr, 'rb') as fp:
            content = fp.read()
        if len(content) == 0:
            raise ValueError('No Content!')
        else:
            return content