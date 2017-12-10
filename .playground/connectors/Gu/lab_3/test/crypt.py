from ..factory.CertFactory import CertFactory
from ..utils.CryptoUtil import CryptoUtil

if __name__ == '__main__':
    cf = CertFactory()
    cert = cf.getCertsForAddr('bb8.csr')
    # print(cert)
    prik = cf.getPrivateKeyForAddr('bb8_prik.pem')
    # pubk = cf.getPublicKeyForAddr('bb8_pubk.pem')
    # print(pubk)
    pubk = cf.getPubkFromCert(cert)


    p_text = b'hello world 123'
    c_text = CryptoUtil.Encrypt(pubk, p_text)
    p1_text = CryptoUtil.Decrypt(prik, c_text)
    print(p_text == p1_text)