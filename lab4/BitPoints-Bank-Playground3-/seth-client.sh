# Configurations
certPath="certs/signed_certs/signed.cert"
keyPath="certs/signed_certs/CA-prikey"
badCert="certs/signed_certs/signed-server.cert"

python3 OnlineBank.py client 20174.1.1337.1 $certPath sethuser
