# Configurations
certPath="certs/signed_certs/signed.cert"
keyPath="certs/signed_certs/CA-prikey"
badCert="certs/signed_certs/signed-server.cert"
python3 OnlineBank.py server pwds test_bankcore_db $certPath $certPath
