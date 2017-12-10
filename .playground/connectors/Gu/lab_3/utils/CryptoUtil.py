import base64
from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.PublicKey import RSA


class CryptoUtil(object):

    def __init__(self):
        super(CryptoUtil, self).__init__()

    @classmethod
    def RSAEncrypt(cls, key, plain_text):
        rsa_key = RSA.importKey(key)
        cipher = Cipher_pkcs1_v1_5.new(rsa_key)
        cipher_text = base64.b64encode(cipher.encrypt(plain_text))
        return cipher_text

    @classmethod
    def RSADecrypt(cls, key, cipher_text):
        random_generator = Random.new().read
        rsa_key = RSA.importKey(key)
        cipher = Cipher_pkcs1_v1_5.new(rsa_key)
        plain_text = cipher.decrypt(base64.b64decode(cipher_text), random_generator)
        return plain_text
